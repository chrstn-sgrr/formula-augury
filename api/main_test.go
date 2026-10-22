package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func writeTestArtifact(t *testing.T, dir, id, date string, mock bool) {
	t.Helper()
	body := fmt.Sprintf(`{"mock":%t,"race":{"id":%q,"season":2026,"round":7,"name":"Test GP","circuit":"Test Circuit","location":"Test","date":%q}}`, mock, id, date)
	if err := os.WriteFile(filepath.Join(dir, id+".json"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}

func TestHealth(t *testing.T) {
	rec := httptest.NewRecorder()
	newServer(t.TempDir()).ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/healthz", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rec.Code)
	}
}

func TestRaceList(t *testing.T) {
	dir := t.TempDir()
	writeTestArtifact(t, dir, "2026-07-barcelona", "2026-06-14", true)
	writeTestArtifact(t, dir, "2026-08-austria", "2026-06-28", false)

	rec := httptest.NewRecorder()
	newServer(dir).ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/races", nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rec.Code)
	}

	var races []raceSummary
	if err := json.Unmarshal(rec.Body.Bytes(), &races); err != nil {
		t.Fatal(err)
	}
	if len(races) != 2 {
		t.Fatalf("races = %d, want 2", len(races))
	}
	if races[0].ID != "2026-08-austria" {
		t.Fatalf("first race = %s, want latest race", races[0].ID)
	}
	if !races[1].Mock {
		t.Fatal("barcelona should be marked mock")
	}
}

func TestRaceArtifact(t *testing.T) {
	dir := t.TempDir()
	id := "2026-07-barcelona"
	writeTestArtifact(t, dir, id, "2026-06-14", true)

	rec := httptest.NewRecorder()
	newServer(dir).ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/races/"+id, nil))
	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", rec.Code)
	}
	if got := rec.Header().Get("Content-Type"); got != "application/json; charset=utf-8" {
		t.Fatalf("content type = %q", got)
	}

	var meta artifactMeta
	if err := json.Unmarshal(rec.Body.Bytes(), &meta); err != nil {
		t.Fatal(err)
	}
	if meta.Race.ID != id {
		t.Fatalf("race id = %q, want %q", meta.Race.ID, id)
	}
}

func TestRaceNotFound(t *testing.T) {
	rec := httptest.NewRecorder()
	newServer(t.TempDir()).ServeHTTP(rec, httptest.NewRequest(http.MethodGet, "/api/races/2026-07-barcelona", nil))
	if rec.Code != http.StatusNotFound {
		t.Fatalf("status = %d, want 404", rec.Code)
	}
}

func TestRaceIDValidation(t *testing.T) {
	s := &server{artifactsDir: t.TempDir()}
	req := httptest.NewRequest(http.MethodGet, "/api/races/x", nil)
	req.SetPathValue("id", "../secret")
	rec := httptest.NewRecorder()
	s.handleRace(rec, req)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want 400", rec.Code)
	}
}
