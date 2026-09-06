import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link, useLocation } from 'react-router-dom'
import { apiFetch } from '../api'
import Header from '../components/Header'

function StudyHome() {
  const { studyId } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const [study, setStudy] = useState(null)
  const successMsg = location.state?.successMsg || null

  // Pagination & Filter state for Active Study Randomized Records
  const [page, setPage] = useState(1)
  const [perPage, setPerPage] = useState(20)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('') // '' | 'assigned' | 'unassigned'
  const [recordsData, setRecordsData] = useState(null)
  const [loadingRecords, setLoadingRecords] = useState(false)

  // Fetch Study details
  useEffect(() => {
    apiFetch(`/organizer/studies/${studyId}`)
      .then((res) => {
        if (!res.ok) {
          navigate('/organizer/home', { replace: true })
          return null
        }
        return res.json()
      })
      .then((data) => {
        if (data) setStudy(data)
      })
      .catch(() => navigate('/organizer/home', { replace: true }))
  }, [studyId, navigate])

  // Fetch Randomized Sequence Records if Study is Active
  useEffect(() => {
    if (!study || study.status !== 'Active') return

    setLoadingRecords(true)
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
    })
    if (search.trim()) params.append('search', search.trim())
    if (statusFilter) params.append('status_filter', statusFilter)

    apiFetch(`/organizer/studies/${studyId}/randomization-records?${params.toString()}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setRecordsData(data)
      })
      .catch(() => {})
      .finally(() => setLoadingRecords(false))
  }, [studyId, study, page, perPage, search, statusFilter])

  // Reset page to 1 when search or statusFilter changes
  function handleSearchChange(e) {
    setSearch(e.target.value)
    setPage(1)
  }

  function handleFilterChange(filter) {
    setStatusFilter(filter)
    setPage(1)
  }

  function handlePerPageChange(e) {
    setPerPage(parseInt(e.target.value, 10))
    setPage(1)
  }

  return (
    <>
      <Header />
      <main className="app">
        <div className="page-header">
          <Link to="/organizer/home" className="back-link">
            ← Back to Studies
          </Link>
          <h1>{study ? study.title : 'Loading…'}</h1>
        </div>

        {successMsg && <p className="success-msg">{successMsg}</p>}

        {study && (
          <>
            {/* Study meta status bar */}
            <div className="status-card" style={{ marginBottom: '24px', maxWidth: 'none' }}>
              <div className="label">Protocol Overview</div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
                <p className="message" style={{ margin: 0 }}>
                  <strong>{study.protocol_code}</strong>
                  {' · '}
                  <span className={`badge badge--${study.status === 'Active' ? 'active' : 'inactive'}`}>
                    {study.status}
                  </span>
                  {' · '}
                  <span>{study.blinding_type}</span>
                  {study.status === 'Active' && (
                    <span style={{ marginLeft: '12px', fontSize: '13px', color: '#555', fontWeight: 600 }}>
                      [Setup Locked]
                    </span>
                  )}
                </p>

                {study.status === 'Draft' && (
                  <span style={{ fontSize: '13px', color: '#555', fontStyle: 'italic' }}>
                    Draft Mode — Complete setup to activate study
                  </span>
                )}
              </div>
            </div>

            {/* IF STUDY IS DRAFT: SHOW STUDY SETUP */}
            {study.status === 'Draft' ? (
              <>
                <div className="section-header">
                  <h2 className="section-title">Study Setup</h2>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '16px' }}>
                  {/* Treatment Arms */}
                  <div className="study-form-card" style={{ maxWidth: 'none' }}>
                    <div className="setup-card__header">
                      <span className="setup-badge">Arms</span>
                      <h2 style={{ marginTop: '8px', fontSize: '15px' }}>Treatment Arms</h2>
                      <p style={{ marginTop: '4px' }}>
                        Define the treatment arms and allocation ratios for this trial.
                      </p>
                    </div>
                    <div style={{ padding: '16px 20px' }}>
                      <Link
                        id="btn-study-arms"
                        to={`/organizer/studies/${studyId}/arms`}
                        className="btn-primary"
                        style={{ textDecoration: 'none' }}
                      >
                        Manage Arms
                      </Link>
                    </div>
                  </div>

                  {/* Randomization */}
                  <div className="study-form-card" style={{ maxWidth: 'none' }}>
                    <div className="setup-card__header">
                      <span className="setup-badge">Randomization</span>
                      <h2 style={{ marginTop: '8px', fontSize: '15px' }}>Randomization Settings</h2>
                      <p style={{ marginTop: '4px' }}>
                        Configure the randomization method, block sizing, and target sample size.
                      </p>
                    </div>
                    <div style={{ padding: '16px 20px' }}>
                      <Link
                        id="btn-study-randomization"
                        to={`/organizer/studies/${studyId}/randomization`}
                        className="btn-primary"
                        style={{ textDecoration: 'none' }}
                      >
                        Configure
                      </Link>
                    </div>
                  </div>

                  {/* Upload CSV */}
                  <div className="study-form-card" style={{ maxWidth: 'none' }}>
                    <div className="setup-card__header">
                      <span className="setup-badge">Data</span>
                      <h2 style={{ marginTop: '8px', fontSize: '15px' }}>Upload CSV</h2>
                      <p style={{ marginTop: '4px' }}>
                        Import a pre-randomized sequence from a CSV file.
                      </p>
                    </div>
                    <div style={{ padding: '16px 20px' }}>
                      <Link
                        id="btn-study-upload"
                        to={`/organizer/studies/${studyId}/upload-csv`}
                        className="btn-primary"
                        style={{ textDecoration: 'none' }}
                      >
                        Upload CSV
                      </Link>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              /* IF STUDY IS ACTIVE: SHOW RANDOMIZED SEQUENCE RECORDS DATA TABLE */
              <>
                {/* Stats Summary Cards */}
                {recordsData && (
                  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${recordsData.unblinded_count > 0 ? 4 : 3}, 1fr)`, gap: '16px', marginBottom: '24px' }}>
                    <div className="status-card" style={{ maxWidth: 'none', margin: 0 }}>
                      <div className="label">Total Sequence Records</div>
                      <div style={{ fontSize: '24px', fontWeight: 600, color: '#1a1a2e', marginTop: '4px' }}>{recordsData.total_count}</div>
                    </div>
                    <div className="status-card" style={{ maxWidth: 'none', margin: 0 }}>
                      <div className="label">Assigned to Patients</div>
                      <div style={{ fontSize: '24px', fontWeight: 600, color: '#1a1a2e', marginTop: '4px' }}>{recordsData.assigned_count}</div>
                    </div>
                    <div className="status-card" style={{ maxWidth: 'none', margin: 0 }}>
                      <div className="label">Unassigned / Available</div>
                      <div style={{ fontSize: '24px', fontWeight: 600, color: '#1a1a2e', marginTop: '4px' }}>{recordsData.unassigned_count}</div>
                    </div>
                    {recordsData.unblinded_count > 0 && (
                      <div className="status-card" style={{ maxWidth: 'none', margin: 0, borderLeftColor: '#c0392b' }}>
                        <div className="label">Emergency Unblinded</div>
                        <div style={{ fontSize: '24px', fontWeight: 600, color: '#1a1a2e', marginTop: '4px' }}>{recordsData.unblinded_count}</div>
                      </div>
                    )}
                  </div>
                )}

                {/* Arm Breakdown Table */}
                {recordsData && recordsData.arm_counts && recordsData.arm_counts.length > 0 && (
                  <div style={{ marginBottom: '24px' }}>
                    <div className="section-header" style={{ marginBottom: '8px' }}>
                      <h3 className="section-title" style={{ fontSize: '15px' }}>Arm Allocation Breakdown</h3>
                    </div>
                    <div style={{ overflowX: 'auto', border: '1px solid #d0d0d0', borderRadius: '4px' }}>
                      <table className="data-table" style={{ margin: 0 }}>
                        <thead>
                          <tr>
                            <th>Treatment Arm</th>
                            <th>Total Records</th>
                            <th>Assigned</th>
                            <th>Unassigned</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recordsData.arm_counts.map((arm, idx) => (
                            <tr key={idx}>
                              <td style={{ fontWeight: 600 }}>{arm.treatment_name}</td>
                              <td>{arm.total}</td>
                              <td>{arm.assigned}</td>
                              <td>{arm.unassigned}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Main Data Table Container */}
                <div style={{ border: '1px solid #d0d0d0', borderRadius: '4px', overflow: 'hidden', background: '#ffffff' }}>
                  {/* Table Header Controls */}
                  <div style={{ padding: '14px 16px', borderBottom: '1px solid #d0d0d0', background: '#f8f9fa', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <h2 style={{ fontSize: '15px', fontWeight: 600, color: '#1a1a2e', margin: 0 }}>Randomized Sequence Records</h2>
                      <span className="badge badge--active">Active Study</span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                      {/* Status Filter Tabs */}
                      <div style={{ display: 'flex', background: '#e0e0e0', borderRadius: '4px', padding: '2px' }}>
                        {['', 'assigned', 'unassigned', 'blinded', 'unblinded'].map((filter) => (
                          <button
                            key={filter}
                            type="button"
                            onClick={() => handleFilterChange(filter)}
                            style={{
                              border: 'none',
                              background: statusFilter === filter ? '#ffffff' : 'transparent',
                              color: statusFilter === filter ? '#1a1a2e' : '#555',
                              fontWeight: statusFilter === filter ? 600 : 500,
                              padding: '4px 12px',
                              borderRadius: '2px',
                              fontSize: '13px',
                              cursor: 'pointer',
                              transition: 'all 0.15s ease',
                              textTransform: 'capitalize',
                            }}
                          >
                            {filter || 'All'}
                          </button>
                        ))}
                      </div>

                      {/* Search Bar */}
                      <input
                        type="text"
                        placeholder="Search kit, drug, patient..."
                        value={search}
                        onChange={handleSearchChange}
                        className="field input"
                        style={{
                          padding: '6px 10px',
                          fontSize: '13px',
                          border: '1px solid #b0b0b0',
                          borderRadius: '3px',
                          width: '210px',
                          outline: 'none',
                        }}
                      />

                      {/* Per Page Select */}
                      <select
                        value={perPage}
                        onChange={handlePerPageChange}
                        className="select-input"
                        style={{
                          padding: '5px 10px',
                          fontSize: '13px',
                        }}
                      >
                        <option value={10}>10 per page</option>
                        <option value={20}>20 per page</option>
                        <option value={50}>50 per page</option>
                        <option value={100}>100 per page</option>
                      </select>
                    </div>
                  </div>

                  {/* Data Table */}
                  {loadingRecords ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#555', fontSize: '14px' }}>
                      Loading sequence records...
                    </div>
                  ) : recordsData && recordsData.records.length > 0 ? (
                    <div style={{ overflowX: 'auto' }}>
                      <table className="data-table" style={{ margin: 0 }}>
                        <thead>
                          <tr>
                            <th style={{ width: '80px' }}>Seq #</th>
                            <th>Kit Code</th>
                            <th>Treatment Arm</th>
                            <th>Blind Status</th>
                            <th>Patient ID</th>
                            <th>Investigator ID</th>
                            <th>Assigned Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recordsData.records.map((rec) => (
                            <tr key={rec.id}>
                              <td style={{ fontWeight: 600 }}>#{rec.sequence_number}</td>
                              <td style={{ fontFamily: 'monospace' }}>{rec.kit_code}</td>
                              <td>{rec.treatment_name}</td>
                              <td>
                                {rec.blind ? (
                                  'Blinded'
                                ) : (
                                  <span className="badge badge--inactive" style={{ color: '#c0392b', borderColor: '#c0392b', background: 'transparent' }}>
                                    UNBLINDED
                                  </span>
                                )}
                              </td>
                              <td>
                                {rec.assigned_patient_id ? (
                                  <strong style={{ color: '#1a1a2e' }}>{rec.assigned_patient_id}</strong>
                                ) : (
                                  <span style={{ color: '#888', fontStyle: 'italic' }}>Unassigned</span>
                                )}
                              </td>
                              <td>
                                {rec.assigned_by_investigator_username ? (
                                  rec.assigned_by_investigator_username
                                ) : rec.assigned_by_investigator_id ? (
                                  `ID #${rec.assigned_by_investigator_id}`
                                ) : (
                                  <span style={{ color: '#888' }}>—</span>
                                )}
                              </td>
                              <td style={{ color: '#555' }}>
                                {rec.assigned_at ? new Date(rec.assigned_at).toLocaleString() : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div style={{ padding: '40px 20px', textAlign: 'center', color: '#555' }}>
                      <p style={{ margin: 0, fontSize: '14px', fontWeight: 500 }}>No sequence records match your filter.</p>
                      {search && <p style={{ fontSize: '13px', marginTop: '4px', color: '#888' }}>Try clearing your search query "{search}".</p>}
                    </div>
                  )}

                  {/* Pagination Footer */}
                  {recordsData && recordsData.total_pages > 1 && (
                    <div style={{ padding: '12px 16px', borderTop: '1px solid #d0d0d0', background: '#f8f9fa', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ fontSize: '13px', color: '#555' }}>
                        Showing <strong>{(recordsData.page - 1) * recordsData.per_page + 1}</strong>–<strong>{Math.min(recordsData.page * recordsData.per_page, recordsData.total_count)}</strong> of <strong>{recordsData.total_count}</strong> records
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          type="button"
                          disabled={recordsData.page <= 1 || loadingRecords}
                          onClick={() => setPage((p) => Math.max(p - 1, 1))}
                          className="btn-secondary"
                        >
                          Previous
                        </button>
                        <span style={{ fontSize: '13px', color: '#333', fontWeight: 600, padding: '0 4px' }}>
                          Page {recordsData.page} of {recordsData.total_pages}
                        </span>
                        <button
                          type="button"
                          disabled={recordsData.page >= recordsData.total_pages || loadingRecords}
                          onClick={() => setPage((p) => Math.min(p + 1, recordsData.total_pages))}
                          className="btn-secondary"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </>
        )}
      </main>
    </>
  )
}

export default StudyHome
