package main

import (
	"encoding/json"
	"errors"
	"flag"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"time"
)

var artifactIDPattern = regexp.MustCompile(`^[0-9]{4}-[0-9]{2}-[a-z0-9-]+$`)

type raceSummary struct {
	ID       string `json:"id"`
	Season   int    `json:"season"`
	Round    int    `json:"round"`
	Name     string `json:"name"`
	Circuit  string `json:"circuit"`
	Location string `json:"location"`
	Date     string `json:"date"`
	Mock     bool   `json:"mock"`
}

type artifactMeta struct {
	Mock bool `json:"mock"`
	Race struct {
		ID       string `json:"id"`
		Season   int    `json:"season"`
		Round    int    `json:"round"`
		Name     string `json:"name"`
		Circuit  string `json:"circuit"`
		Location string `json:"location"`
		Date     string `json:"date"`
	} `json:"race"`
}

type server struct {
	artifactsDir string
	mux          *http.ServeMux
}

func newServer(artifactsDir string) http.Handler {
	s := &server{artifactsDir: artifactsDir, mux: http.NewServeMux()}
	s.mux.HandleFunc("GET /healthz", s.handleHealth)
	s.mux.HandleFunc("GET /api/races", s.handleRaces)
	s.mux.HandleFunc("GET /api/races/{id}", s.handleRace)
	return s.mux
}

func (s *server) handleHealth(w http.ResponseWriter, _ *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (s *server) handleRaces(w http.ResponseWriter, _ *http.Request) {
	entries, err := os.ReadDir(s.artifactsDir)
	if err != nil {
		log.Printf("read artifacts directory: %v", err)
		writeError(w, http.StatusInternalServerError, "could not read artifacts")
		return
	}

	races := make([]raceSummary, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() || filepath.Ext(entry.Name()) != ".json" {
			continue
		}
		path := filepath.Join(s.artifactsDir, entry.Name())
		_, meta, err := readArtifact(path)
		if err != nil {
			log.Printf("skip artifact %s: %v", path, err)
			continue
		}
		races = append(races, raceSummary{
			ID:       meta.Race.ID,
			Season:   meta.Race.Season,
			Round:    meta.Race.Round,
			Name:     meta.Race.Name,
			Circuit:  meta.Race.Circuit,
			Location: meta.Race.Location,
			Date:     meta.Race.Date,
			Mock:     meta.Mock,
		})
	}

	sort.Slice(races, func(i, j int) bool {
		if races[i].Date != races[j].Date {
			return races[i].Date > races[j].Date
		}
		if races[i].Season != races[j].Season {
			return races[i].Season > races[j].Season
		}
		if races[i].Round != races[j].Round {
			return races[i].Round > races[j].Round
		}
		return races[i].ID < races[j].ID
	})

	writeJSON(w, http.StatusOK, races)
}

func (s *server) handleRace(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if !artifactIDPattern.MatchString(id) {
		writeError(w, http.StatusBadRequest, "invalid race id")
		return
	}

	path := filepath.Join(s.artifactsDir, id+".json")
	data, meta, err := readArtifact(path)
	if errors.Is(err, os.ErrNotExist) {
		writeError(w, http.StatusNotFound, "race not found")
		return
	}
	if err != nil {
		log.Printf("read artifact %s: %v", path, err)
		writeError(w, http.StatusInternalServerError, "could not read race")
		return
	}
	if meta.Race.ID != id {
		log.Printf("artifact id mismatch: file %s has id %q", path, meta.Race.ID)
		writeError(w, http.StatusInternalServerError, "artifact id mismatch")
		return
	}

	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "public, max-age=300")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(http.StatusOK)
	if _, err := w.Write(data); err != nil {
		log.Printf("write artifact %s: %v", path, err)
	}
}

func readArtifact(path string) ([]byte, artifactMeta, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, artifactMeta{}, err
	}
	var meta artifactMeta
	if err := json.Unmarshal(data, &meta); err != nil {
		return nil, meta, err
	}
	if meta.Race.ID == "" {
		return nil, meta, errors.New("missing race.id")
	}
	return data, meta, nil
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(value); err != nil {
		log.Printf("encode response: %v", err)
	}
}

func writeError(w http.ResponseWriter, status int, message string) {
	writeJSON(w, status, map[string]string{"error": message})
}

func main() {
	addr := flag.String("addr", envOr("ADDR", ":8080"), "listen address")
	artifactsDir := flag.String("artifacts", envOr("ARTIFACTS_DIR", "data/artifacts"), "directory containing forecast artifacts")
	flag.Parse()

	srv := &http.Server{
		Addr:              *addr,
		Handler:           newServer(*artifactsDir),
		ReadHeaderTimeout: 5 * time.Second,
		IdleTimeout:       60 * time.Second,
	}
	log.Printf("formula-augury API on %s (artifacts: %s)", *addr, *artifactsDir)
	if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Fatal(err)
	}
}

func envOr(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
