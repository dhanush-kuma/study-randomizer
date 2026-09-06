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
                    <span style={{ marginLeft: '12px', fontSize: '13px', color: '#166534', fontWeight: 600, background: '#f0fdf4', padding: '2px 8px', borderRadius: '4px', border: '1px solid #bbf7d0' }}>
                      🔒 Setup Locked
                    </span>
                  )}
                </p>

                {study.status === 'Draft' && (
                  <span style={{ fontSize: '13px', color: '#854d0e', background: '#fef9c3', padding: '4px 10px', borderRadius: '4px', border: '1px solid #fef08a' }}>
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
                        Manage Arms →
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
                        Configure →
                      </Link>
                    </div>
                  </div>

                  {/* Upload CSV */}
                  <div className="study-form-card" style={{ maxWidth: 'none' }}>
                    <div className="setup-card__header">
                      <span className="setup-badge">Data</span>
                      <h2 style={{ marginTop: '8px', fontSize: '15px' }}>Upload CSV</h2>
                      <p style={{ marginTop: '4px' }}>
                        Import participant data or baseline sequence from a CSV file.
                      </p>
                    </div>
                    <div style={{ padding: '16px 20px' }}>
                      <Link
                        id="btn-study-upload"
                        to={`/organizer/studies/${studyId}/upload-csv`}
                        className="btn-primary"
                        style={{ textDecoration: 'none' }}
                      >
                        Upload CSV →
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
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
                    <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Total Sequence Records</div>
                      <div style={{ fontSize: '28px', fontWeight: 700, color: '#0f172a', marginTop: '4px' }}>{recordsData.total_count}</div>
                    </div>
                    <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#15803d', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Assigned to Patients</div>
                      <div style={{ fontSize: '28px', fontWeight: 700, color: '#166534', marginTop: '4px' }}>{recordsData.assigned_count}</div>
                    </div>
                    <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px 20px' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#b45309', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Unassigned / Available</div>
                      <div style={{ fontSize: '28px', fontWeight: 700, color: '#92400e', marginTop: '4px' }}>{recordsData.unassigned_count}</div>
                    </div>
                  </div>
                )}

                {/* Main Data Table Container */}
                <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
                  {/* Table Header Controls */}
                  <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <h2 style={{ fontSize: '17px', fontWeight: 600, color: '#0f172a', margin: 0 }}>Randomized Sequence Records</h2>
                      <span style={{ fontSize: '12px', color: '#64748b', background: '#e2e8f0', padding: '2px 8px', borderRadius: '12px', fontWeight: 500 }}>
                        Active Study
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                      {/* Status Filter Tabs */}
                      <div style={{ display: 'flex', background: '#e2e8f0', borderRadius: '6px', padding: '2px' }}>
                        <button
                          type="button"
                          onClick={() => handleFilterChange('')}
                          style={{
                            border: 'none',
                            background: statusFilter === '' ? '#ffffff' : 'transparent',
                            color: statusFilter === '' ? '#0f172a' : '#64748b',
                            fontWeight: statusFilter === '' ? 600 : 500,
                            padding: '4px 12px',
                            borderRadius: '4px',
                            fontSize: '13px',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          All
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFilterChange('assigned')}
                          style={{
                            border: 'none',
                            background: statusFilter === 'assigned' ? '#ffffff' : 'transparent',
                            color: statusFilter === 'assigned' ? '#166534' : '#64748b',
                            fontWeight: statusFilter === 'assigned' ? 600 : 500,
                            padding: '4px 12px',
                            borderRadius: '4px',
                            fontSize: '13px',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          Assigned
                        </button>
                        <button
                          type="button"
                          onClick={() => handleFilterChange('unassigned')}
                          style={{
                            border: 'none',
                            background: statusFilter === 'unassigned' ? '#ffffff' : 'transparent',
                            color: statusFilter === 'unassigned' ? '#92400e' : '#64748b',
                            fontWeight: statusFilter === 'unassigned' ? 600 : 500,
                            padding: '4px 12px',
                            borderRadius: '4px',
                            fontSize: '13px',
                            cursor: 'pointer',
                            transition: 'all 0.15s ease',
                          }}
                        >
                          Unassigned
                        </button>
                      </div>

                      {/* Search Bar */}
                      <input
                        type="text"
                        placeholder="Search kit, drug, patient..."
                        value={search}
                        onChange={handleSearchChange}
                        style={{
                          padding: '6px 12px',
                          fontSize: '13px',
                          border: '1px solid #cbd5e1',
                          borderRadius: '6px',
                          width: '210px',
                          outline: 'none',
                        }}
                      />

                      {/* Per Page Select */}
                      <select
                        value={perPage}
                        onChange={handlePerPageChange}
                        style={{
                          padding: '6px 10px',
                          fontSize: '13px',
                          border: '1px solid #cbd5e1',
                          borderRadius: '6px',
                          background: '#ffffff',
                          color: '#334155',
                          outline: 'none',
                          cursor: 'pointer',
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
                    <div style={{ padding: '40px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>
                      Loading sequence records…
                    </div>
                  ) : recordsData && recordsData.records.length > 0 ? (
                    <div style={{ overflowX: 'auto' }}>
                      <table className="investigator-table" style={{ width: '100%', margin: 0, borderCollapse: 'collapse' }}>
                        <thead>
                          <tr style={{ background: '#f1f5f9', borderBottom: '1px solid #e2e8f0', textAlign: 'left', fontSize: '12px', textTransform: 'uppercase', color: '#475569', letterSpacing: '0.5px' }}>
                            <th style={{ padding: '12px 16px', width: '100px' }}>Seq #</th>
                            <th style={{ padding: '12px 16px' }}>Kit Code</th>
                            <th style={{ padding: '12px 16px' }}>Drug / Treatment Arm</th>
                            <th style={{ padding: '12px 16px' }}>Patient ID</th>
                            <th style={{ padding: '12px 16px' }}>Investigator ID</th>
                            <th style={{ padding: '12px 16px' }}>Assigned Date</th>
                          </tr>
                        </thead>
                        <tbody>
                          {recordsData.records.map((rec) => (
                            <tr key={rec.id} style={{ borderBottom: '1px solid #f1f5f9', fontSize: '14px', color: '#334155' }}>
                              <td style={{ padding: '12px 16px', fontWeight: 600, color: '#0f172a' }}>
                                #{rec.sequence_number}
                              </td>
                              <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontWeight: 600, color: '#1e293b' }}>
                                {rec.kit_code}
                              </td>
                              <td style={{ padding: '12px 16px' }}>
                                <span style={{ background: '#e0f2fe', color: '#0369a1', fontWeight: 500, padding: '3px 8px', borderRadius: '4px', fontSize: '13px' }}>
                                  {rec.treatment_name}
                                </span>
                              </td>
                              <td style={{ padding: '12px 16px' }}>
                                {rec.assigned_patient_id ? (
                                  <span style={{ fontWeight: 600, color: '#0f172a' }}>{rec.assigned_patient_id}</span>
                                ) : (
                                  <span style={{ color: '#94a3b8', fontStyle: 'italic', fontSize: '13px' }}>— Unassigned —</span>
                                )}
                              </td>
                              <td style={{ padding: '12px 16px' }}>
                                {rec.assigned_by_investigator_username ? (
                                  <span style={{ fontWeight: 500, color: '#475569' }}>
                                    {rec.assigned_by_investigator_username}
                                  </span>
                                ) : rec.assigned_by_investigator_id ? (
                                  <span style={{ fontWeight: 500, color: '#475569' }}>
                                    ID #{rec.assigned_by_investigator_id}
                                  </span>
                                ) : (
                                  <span style={{ color: '#94a3b8' }}>—</span>
                                )}
                              </td>
                              <td style={{ padding: '12px 16px', color: '#64748b', fontSize: '13px' }}>
                                {rec.assigned_at ? new Date(rec.assigned_at).toLocaleString() : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div style={{ padding: '40px 20px', textAlign: 'center', color: '#64748b' }}>
                      <p style={{ margin: 0, fontSize: '15px', fontWeight: 500 }}>No sequence records match your filter.</p>
                      {search && <p style={{ fontSize: '13px', marginTop: '4px' }}>Try clearing your search query "{search}".</p>}
                    </div>
                  )}

                  {/* Pagination Footer */}
                  {recordsData && recordsData.total_pages > 1 && (
                    <div style={{ padding: '12px 20px', borderTop: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ fontSize: '13px', color: '#64748b' }}>
                        Showing <strong>{(recordsData.page - 1) * recordsData.per_page + 1}</strong>–<strong>{Math.min(recordsData.page * recordsData.per_page, recordsData.total_count)}</strong> of <strong>{recordsData.total_count}</strong> records
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          type="button"
                          disabled={recordsData.page <= 1 || loadingRecords}
                          onClick={() => setPage((p) => Math.max(p - 1, 1))}
                          className="btn-secondary"
                          style={{ padding: '4px 12px', fontSize: '13px' }}
                        >
                          ‹ Previous
                        </button>
                        <span style={{ fontSize: '13px', color: '#475569', fontWeight: 500, padding: '0 4px' }}>
                          Page {recordsData.page} of {recordsData.total_pages}
                        </span>
                        <button
                          type="button"
                          disabled={recordsData.page >= recordsData.total_pages || loadingRecords}
                          onClick={() => setPage((p) => Math.min(p + 1, recordsData.total_pages))}
                          className="btn-secondary"
                          style={{ padding: '4px 12px', fontSize: '13px' }}
                        >
                          Next ›
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
