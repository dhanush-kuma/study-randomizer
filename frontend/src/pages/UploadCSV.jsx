import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiFetch, apiUpload } from '../api'
import Header from '../components/Header'

// --- Sample CSV content (embedded so no static file config needed) ---
const SAMPLE_CSV_CONTENT = `sequence_number,kit_code,treatment_arm
1,KIT-DA,Drug A
2,KIT-PBO,Placebo
3,KIT-PBO,Placebo
4,KIT-DA,Drug A
5,KIT-DA,Drug A
6,KIT-PBO,Placebo
7,KIT-PBO,Placebo
8,KIT-DA,Drug A
9,KIT-DA,Drug A
10,KIT-PBO,Placebo
11,KIT-PBO,Placebo
12,KIT-DA,Drug A
`

function downloadSampleCsv() {
  const blob = new Blob([SAMPLE_CSV_CONTENT], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'sample_randomization.csv'
  a.click()
  URL.revokeObjectURL(url)
}

// Parse CSV text into { headers, rows } for the preview table
function parseCsvPreview(text) {
  const lines = text.trim().split('\n').filter(Boolean)
  if (lines.length === 0) return { headers: [], rows: [] }
  const headers = lines[0].split(',').map((h) => h.trim())
  const rows = lines.slice(1).map((line) =>
    line.split(',').map((cell) => cell.trim())
  )
  return { headers, rows }
}

function UploadCSV() {
  const { studyId } = useParams()
  const navigate = useNavigate()

  const [study, setStudy] = useState(null)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)   // { headers, rows }
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState(null)     // CsvUploadResponse
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  useEffect(() => {
    apiFetch(`/organizer/studies/${studyId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => { if (data) setStudy(data) })
      .catch(() => navigate('/organizer/home', { replace: true }))
  }, [studyId, navigate])

  function handleFileChange(e) {
    setError(null)
    setResult(null)
    const selected = e.target.files?.[0] ?? null
    setFile(selected)

    if (!selected) {
      setPreview(null)
      return
    }

    if (!selected.name.toLowerCase().endsWith('.csv')) {
      setError('Please select a .csv file.')
      setFile(null)
      setPreview(null)
      return
    }

    const reader = new FileReader()
    reader.onload = (ev) => {
      const text = ev.target.result
      setPreview(parseCsvPreview(text))
    }
    reader.readAsText(selected)
  }

  async function handleUpload(e) {
    e.preventDefault()
    if (!file) return

    setError(null)
    setResult(null)
    setUploading(true)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await apiUpload(
        `/organizer/studies/${studyId}/upload-randomization-csv`,
        formData
      )

      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || `Upload failed (${res.status}).`)
        return
      }

      setResult(data)
      // Refresh study to pick up status change
      apiFetch(`/organizer/studies/${studyId}`)
        .then((r) => (r.ok ? r.json() : null))
        .then((d) => { if (d) setStudy(d) })
    } catch {
      setError('Could not connect to backend.')
    } finally {
      setUploading(false)
    }
  }

  function handleReset() {
    setFile(null)
    setPreview(null)
    setError(null)
    setResult(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const PREVIEW_LIMIT = 5

  return (
    <>
      <Header />
      <main className="app">
        <div className="page-header">
          <Link to={`/organizer/studies/${studyId}/home`} className="back-link">
            Back to Study
          </Link>
          <h1>{study ? study.title : 'Loading...'} - Upload Randomization</h1>
        </div>

        {!study ? (
          <p className="loading">Loading study...</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '760px' }}>
            {study.status === 'Active' && (
              <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '12px 16px', color: '#991b1b', fontSize: '14px' }}>
                <strong>Study is Active and locked.</strong> Sequence records have already been uploaded and finalized. Re-uploading is disabled.
              </div>
            )}

            {/* ── Instructions card ─────────────────────────────── */}
            <div className="setup-card">
              <div className="setup-card__header">
                <span className="setup-badge">Format</span>
                <h2 style={{ marginTop: '8px' }}>CSV Format Requirements</h2>
                <p>Use this page to upload a pre-randomized sequence directly into the study.</p>
              </div>
              <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <ul className="csv-instructions">
                  <li>File must be <strong>.csv</strong> with a header row as the first line.</li>
                  <li>Required columns: <code>sequence_number</code>, <code>kit_code</code>, <code>treatment_arm</code></li>
                  <li><code>kit_code</code> identifies the treatment kit — the same value repeats for every row in the same arm (e.g. <code>KIT-DA</code> for all Drug A rows).</li>
                  <li><code>treatment_arm</code> is the display name of the arm (e.g. <em>Drug A</em>, <em>Placebo</em>).</li>
                  <li>Re-uploading <strong>replaces</strong> all existing records for this study.</li>
                  <li>On success, study status is set to <strong>Active</strong>.</li>
                </ul>

                <div>
                  <button
                    id="btn-download-sample"
                    type="button"
                    className="btn-secondary"
                    onClick={downloadSampleCsv}
                    style={{ fontSize: '13px' }}
                  >
                    Download Sample CSV
                  </button>
                </div>
              </div>
            </div>

            {/* ── Upload card ────────────────────────────────────── */}
            {!result && study.status !== 'Active' && (
              <div className="setup-card">
                <div className="setup-card__header">
                  <span className="setup-badge">Upload</span>
                  <h2 style={{ marginTop: '8px' }}>Select CSV File</h2>
                  <p>Choose your randomization CSV file to preview and upload.</p>
                </div>
                <form className="setup-form" onSubmit={handleUpload} noValidate>
                  {error && <p className="error">{error}</p>}

                  <div className="field csv-upload-area">
                    <label htmlFor="csv-file-input">CSV File</label>
                    <input
                      id="csv-file-input"
                      ref={fileInputRef}
                      type="file"
                      accept=".csv"
                      onChange={handleFileChange}
                    />
                    {file && (
                      <span className="field-hint">
                        Selected: <strong>{file.name}</strong> ({(file.size / 1024).toFixed(1)} KB)
                      </span>
                    )}
                  </div>

                  {/* Preview table */}
                  {preview && preview.rows.length > 0 && (
                    <div>
                      <p className="field-hint" style={{ marginBottom: '8px' }}>
                        Preview — first {Math.min(PREVIEW_LIMIT, preview.rows.length)} of {preview.rows.length} row(s):
                      </p>
                      <div style={{ overflowX: 'auto' }}>
                        <table className="data-table" style={{ minWidth: '400px' }}>
                          <thead>
                            <tr>
                              {preview.headers.map((h) => (
                                <th key={h}>{h}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {preview.rows.slice(0, PREVIEW_LIMIT).map((row, i) => (
                              <tr key={i}>
                                {row.map((cell, j) => (
                                  <td key={j}>{cell}</td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {preview.rows.length > PREVIEW_LIMIT && (
                        <p className="field-hint" style={{ marginTop: '6px' }}>
                          … and {preview.rows.length - PREVIEW_LIMIT} more row(s) not shown.
                        </p>
                      )}
                    </div>
                  )}

                  <div className="form-actions">
                    <button
                      id="btn-upload-csv"
                      type="submit"
                      className="btn-primary"
                      disabled={!file || uploading}
                    >
                      {uploading ? 'Uploading...' : 'Upload and Activate Study'}
                    </button>
                    {file && (
                      <button
                        type="button"
                        className="btn-secondary"
                        onClick={handleReset}
                        disabled={uploading}
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </form>
              </div>
            )}

            {/* ── Success result card ────────────────────────────── */}
            {result && (
              <div className="setup-card">
                <div className="setup-card__header" style={{ borderLeft: '4px solid #1a6b2a' }}>
                  <span className="setup-badge" style={{ background: '#1a6b2a' }}>Success</span>
                  <h2 style={{ marginTop: '8px' }}>Upload Complete</h2>
                  <p>
                    <strong>{result.inserted_count}</strong> record(s) inserted.{' '}
                    Study status is now{' '}
                    <span className="badge badge--active">{result.study_status}</span>.
                  </p>
                </div>

                <div style={{ overflowX: 'auto', padding: '16px 20px' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Kit Code</th>
                        <th>Treatment</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.records.map((rec) => (
                        <tr key={rec.id}>
                          <td>{rec.sequence_number}</td>
                          <td><code>{rec.kit_code}</code></td>
                          <td>{rec.treatment_name}</td>
                          <td>
                            <span className="badge badge--inactive">Unassigned</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={{ padding: '0 20px 20px', display: 'flex', gap: '10px' }}>
                  <Link
                    to={`/organizer/studies/${studyId}/home`}
                    className="btn-primary"
                    style={{ textDecoration: 'none' }}
                  >
                    Back to Study
                  </Link>
                  <button
                    id="btn-upload-another"
                    type="button"
                    className="btn-secondary"
                    onClick={handleReset}
                  >
                    Upload New File
                  </button>
                </div>
              </div>
            )}

          </div>
        )}
      </main>
    </>
  )
}

export default UploadCSV
