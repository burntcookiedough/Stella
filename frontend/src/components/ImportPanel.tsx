import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { uploadImport } from "../api/client";

const SOURCE_OPTIONS = [
  { value: "fitbit", label: "Fitbit" },
  { value: "apple_health", label: "Apple Health" },
  { value: "google_health", label: "Google Health" },
  { value: "oura", label: "Oura" },
  { value: "garmin", label: "Garmin" },
  { value: "manual", label: "Manual CSV" },
];

export function ImportPanel() {
  const [source, setSource] = useState("fitbit");
  const [files, setFiles] = useState<File[]>([]);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => uploadImport(files, source),
    onSuccess: async () => {
      setFiles([]);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["overview"] }),
        queryClient.invalidateQueries({ queryKey: ["correlations"] }),
      ]);
    },
  });

  return (
    <section className="import-panel">
      <div>
        <p className="eyebrow">Import</p>
        <h3>Bring in exported health data</h3>
      </div>
      <div className="import-controls">
        <select value={source} onChange={(event) => setSource(event.target.value)}>
          {SOURCE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <label className="file-input">
          <span>{files.length ? `${files.length} file(s)` : "Choose files"}</span>
          <input
            type="file"
            multiple
            onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          />
        </label>
        <button
          type="button"
          disabled={!files.length || mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? "Importing..." : "Run import"}
        </button>
      </div>
      {mutation.error ? <p className="status error">{String(mutation.error)}</p> : null}
      {mutation.isSuccess ? <p className="status">Latest import completed.</p> : null}
    </section>
  );
}
