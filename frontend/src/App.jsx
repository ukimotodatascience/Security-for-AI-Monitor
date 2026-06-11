import React, { useState, useEffect } from 'react';

// Icons using inline SVG to keep code standalone and clean
const Icons = {
  Shield: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
  ),
  Overview: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="9" rx="1"/><rect x="14" y="3" width="7" height="5" rx="1"/><rect x="14" y="12" width="7" height="9" rx="1"/><rect x="3" y="16" width="7" height="5" rx="1"/></svg>
  ),
  Bug: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M12 2v9M8 3v4M16 3v4M4 14h16M4 18h16M3 7.5c2.5 1 5 1.5 9 1.5s6.5-.5 9-1.5"/></svg>
  ),
  BookOpen: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2zM22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
  ),
  Globe: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
  ),
  FileText: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
  ),
  Github: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
  ),
  AlertTriangle: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
  ),
  ExternalLink: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
  ),
  Calendar: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
  ),
  ChevronDown: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
  ),
  ChevronUp: () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="18 15 12 9 6 15"/></svg>
  )
};

export default function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterOption, setFilterOption] = useState('all');

  // Vulnerability specific filters
  const [cveSearch, setCveSearch] = useState('');
  const [cveSeverity, setCveSeverity] = useState('all');
  const [cveKevOnly, setCveKevOnly] = useState(false);
  const [expandedCves, setExpandedCves] = useState({});

  useEffect(() => {
    // In production, dashboard_data.json is generated in public/data/
    fetch('data/dashboard_data.json')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load dashboard data. Ensure the pipeline has run successfully.');
        }
        return response.json();
      })
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const toggleCveExpand = (cveId) => {
    setExpandedCves(prev => ({
      ...prev,
      [cveId]: !prev[cveId]
    }));
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', background: '#0a0c10', color: '#f8fafc', flexDirection: 'column', gap: '20px' }}>
        <div style={{ width: '40px', height: '40px', border: '3px solid rgba(6, 182, 212, 0.1)', borderTopColor: '#06b6d4', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
        <p style={{ letterSpacing: '0.05em', fontSize: '0.9rem', color: '#94a3b8' }}>モニターシステムを初期化中...</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', height: '100vh', width: '100vw', alignItems: 'center', justifyContent: 'center', background: '#0a0c10', color: '#f43f5e', flexDirection: 'column', gap: '20px', padding: '40px', textAlign: 'center' }}>
        <Icons.AlertTriangle />
        <h2>モニターシステムの初期化に失敗しました</h2>
        <p style={{ color: '#94a3b8', maxWidth: '500px', fontSize: '0.95rem' }}>{error}</p>
        <p style={{ color: '#64748b', fontSize: '0.85rem' }}>データ収集パイプライン（<code>run_pipeline.py</code>）を実行して、必要なデータファイルを生成してください。</p>
      </div>
    );
  }

  const formatDateTime = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    return date.toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' });
  };

  const formatDateOnly = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP');
  };

  // Helper to render EPSS bar
  const renderEpssBar = (epssObj) => {
    if (!epssObj) return 'N/A';
    const percentage = (epssObj.epss * 100).toFixed(2);
    let color = '#10b981'; // low
    if (epssObj.epss > 0.5) color = '#f43f5e'; // high
    else if (epssObj.epss > 0.1) color = '#f59e0b'; // medium

    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span className="font-mono" style={{ fontSize: '0.85rem', width: '45px' }}>{percentage}%</span>
        <div className="epss-bar-bg">
          <div className="epss-bar-fill" style={{ width: `${Math.min(percentage * 2, 100)}%`, backgroundColor: color }}></div>
        </div>
      </div>
    );
  };

  // 1. Overview Tab Render
  const renderOverview = () => {
    const totalCves = data.meta.totals.cves;
    const totalArxiv = data.meta.totals.arxiv;
    const totalArticles = data.meta.totals.rss_articles;
    const activeKeywords = data.meta.keywords.filter(k => k.status.toLowerCase() === 'active');
    const activeProducts = data.meta.products.filter(p => p.status.toLowerCase() === 'active');

    // Aggregate latest feed (Articles + CVEs + arXiv)
    const recentFeed = [];
    data.cves.slice(0, 5).forEach(cve => {
      recentFeed.push({
        type: 'cve',
        title: `${cve.cve_id}: ${(cve.cvss_base_score !== null && cve.cvss_base_score !== undefined) ? `CVSS ${cve.cvss_base_score}` : 'スコア未設定'} (${cve.cvss_base_label || '不明'})`,
        desc: cve.description,
        date: cve.published_at,
        badge: cve.is_kev ? 'badge-rose' : 'badge-amber',
        badgeText: cve.is_kev ? 'KEV 脆弱性' : 'CVE',
        url: `https://nvd.nist.gov/vuln/detail/${cve.cve_id}`
      });
    });

    data.arxiv.slice(0, 5).forEach(paper => {
      recentFeed.push({
        type: 'arxiv',
        title: paper.title,
        desc: paper.summary,
        date: paper.published_at,
        badge: 'badge-purple',
        badgeText: '研究論文',
        url: paper.abs_url
      });
    });

    data.rss_articles.slice(0, 5).forEach(art => {
      recentFeed.push({
        type: 'article',
        title: art.title,
        desc: art.summary || '要約がありません。',
        date: art.published_at,
        badge: 'badge-blue',
        badgeText: art.source_name || '記事',
        url: art.url
      });
    });

    recentFeed.sort((a, b) => new Date(b.date) - new Date(a.date));

    return (
      <div className="fade-in">
        <div className="stat-grid">
          <div className="glass-panel stat-card">
            <span className="stat-label">監視対象CVE数</span>
            <div className="stat-value">{totalCves}</div>
          </div>
          <div className="glass-panel stat-card">
            <span className="stat-label">収集研究論文数</span>
            <div className="stat-value">{totalArxiv}</div>
          </div>
          <div className="glass-panel stat-card">
            <span className="stat-label">収集RSS記事数</span>
            <div className="stat-value">{totalArticles}</div>
          </div>
          <div className="glass-panel stat-card">
            <span className="stat-label">有効キーワード数</span>
            <div className="stat-value">{activeKeywords.length}</div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '30px', marginTop: '30px' }}>
          {/* Latest Threat Feed */}
          <div className="glass-panel" style={{ padding: '30px' }}>
            <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Icons.Overview />
              最新の脅威フィード（グローバル監視）
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {recentFeed.slice(0, 10).map((item, idx) => (
                <div key={idx} style={{ paddingBottom: '20px', borderBottom: '1px solid var(--border)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                    <span className={`badge ${item.badge}`}>{item.badgeText}</span>
                    <span className="sync-time">{formatDateTime(item.date)}</span>
                  </div>
                  <a href={item.url} target="_blank" rel="noopener noreferrer" className="card-title" style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                    {item.title} <Icons.ExternalLink />
                  </a>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {item.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Configuration Status */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h4 style={{ marginBottom: '16px', fontSize: '0.95rem', letterSpacing: '0.05em' }}>監視対象AI製品</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {activeProducts.map((p, idx) => (
                  <span key={idx} className="badge badge-cyan" style={{ fontSize: '0.8rem' }}>{p.product_name}</span>
                ))}
              </div>
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
              <h4 style={{ marginBottom: '16px', fontSize: '0.95rem', letterSpacing: '0.05em' }}>監視キーワード</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {activeKeywords.map((k, idx) => (
                  <span key={idx} className="badge badge-purple" style={{ fontSize: '0.8rem' }}>{k.keyword}</span>
                ))}
              </div>
            </div>

            {/* GitHub Repos Activities */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h4 style={{ marginBottom: '16px', fontSize: '0.95rem', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Icons.Github />
                GitHubリポジトリ
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {data.github_repos.slice(0, 5).map((repo, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <a href={repo.html_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.9rem', fontWeight: '500', color: 'var(--text-primary)' }}>
                      {repo.full_name}
                    </a>
                    <span className="badge badge-amber">★ {repo.stars}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 2. Vulnerabilities Tab Render
  const renderVulnerabilities = () => {
    // Filter logic
    const filteredCves = data.cves.filter(cve => {
      const matchesSearch = cve.cve_id.toLowerCase().includes(cveSearch.toLowerCase()) ||
        cve.description.toLowerCase().includes(cveSearch.toLowerCase()) ||
        cve.cpe_names.some(cpe => cpe.toLowerCase().includes(cveSearch.toLowerCase()));

      const matchesSeverity = cveSeverity === 'all' ||
        (cve.cvss_base_label && cve.cvss_base_label.toLowerCase() === cveSeverity.toLowerCase());

      const matchesKev = !cveKevOnly || cve.is_kev;

      return matchesSearch && matchesSeverity && matchesKev;
    });

    return (
      <div className="fade-in">
        <div className="search-container">
          <input
            type="text"
            placeholder="CVE ID, CPE製品名, 説明から検索..."
            className="search-input"
            value={cveSearch}
            onChange={(e) => setCveSearch(e.target.value)}
          />
          <select
            className="filter-select"
            value={cveSeverity}
            onChange={(e) => setCveSeverity(e.target.value)}
          >
            <option value="all">すべての深刻度</option>
            <option value="critical">CRITICAL (緊急)</option>
            <option value="high">HIGH (高)</option>
            <option value="medium">MEDIUM (中)</option>
            <option value="low">LOW (低)</option>
          </select>
          <label style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', cursor: 'pointer', userSelect: 'none', background: 'rgba(18, 22, 32, 0.8)', border: '1px solid var(--border)', borderRadius: '10px', padding: '12px 16px', fontSize: '0.95rem' }}>
            <input
              type="checkbox"
              checked={cveKevOnly}
              onChange={(e) => setCveKevOnly(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            CISA KEV のみ
          </label>
        </div>

        <div className="table-container glass-panel">
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}></th>
                <th style={{ width: '150px' }}>CVE ID</th>
                <th style={{ width: '130px' }}>公開日</th>
                <th style={{ width: '120px' }}>CVSS スコア</th>
                <th style={{ width: '160px' }}>EPSS スコア</th>
                <th>説明</th>
                <th style={{ width: '120px' }}>ステータス</th>
              </tr>
            </thead>
            <tbody>
              {filteredCves.length === 0 ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    条件に一致する脆弱性が見つかりませんでした。
                  </td>
                </tr>
              ) : (
                filteredCves.map((cve) => {
                  const isExpanded = !!expandedCves[cve.cve_id];
                  return (
                    <React.Fragment key={cve.cve_id}>
                      <tr
                        onClick={() => toggleCveExpand(cve.cve_id)}
                        style={{ cursor: 'pointer' }}
                      >
                        <td style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                          {isExpanded ? <Icons.ChevronUp /> : <Icons.ChevronDown />}
                        </td>
                        <td className="font-mono" style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>
                          {cve.cve_id}
                        </td>
                        <td style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                          {formatDateOnly(cve.published_at)}
                        </td>
                        <td>
                          {(cve.cvss_base_score !== null && cve.cvss_base_score !== undefined) ? (
                            <span
                              className={`badge ${
                                cve.cvss_base_label === 'CRITICAL' ? 'badge-rose' :
                                cve.cvss_base_label === 'HIGH' ? 'badge-rose' :
                                cve.cvss_base_label === 'MEDIUM' ? 'badge-amber' : 'badge-blue'
                              }`}
                              style={{ fontWeight: 700 }}
                            >
                              {cve.cvss_base_score} {cve.cvss_base_label}
                            </span>
                          ) : (
                            <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-muted)' }}>N/A</span>
                          )}
                        </td>
                        <td>
                          {renderEpssBar(cve.epss)}
                        </td>
                        <td style={{ fontSize: '0.9rem', lineHeight: '1.4', paddingRight: '20px' }}>
                          <div style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                            {cve.description}
                          </div>
                        </td>
                        <td>
                          {cve.is_kev && (
                            <span className="badge badge-rose" style={{ gap: '4px' }}>
                              <Icons.AlertTriangle /> KEV
                            </span>
                          )}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan="7" className="cve-detail-expanded">
                            <div className="fade-in">
                              <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <Icons.Bug /> 脆弱性詳細情報
                              </h4>

                              <p style={{ color: 'var(--text-primary)', fontSize: '0.95rem', lineHeight: '1.6', marginBottom: '20px', background: 'rgba(0,0,0,0.1)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border)' }}>
                                {cve.description}
                              </p>

                              <div className="cve-meta-info">
                                <div>
                                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>最終更新日</span>
                                  <p style={{ fontSize: '0.9rem', marginTop: '4px' }}>{formatDateTime(cve.last_modified_at)}</p>
                                </div>
                                <div>
                                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>CWE（脆弱性タイプ）</span>
                                  <div style={{ marginTop: '4px' }}>
                                    {cve.cwes && cve.cwes.length > 0 ? (
                                      cve.cwes.map((c, i) => (
                                        <div key={i} style={{ fontSize: '0.85rem' }}>
                                          <span className="font-mono" style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{c.cwe_id}</span>: {c.name}
                                        </div>
                                      ))
                                    ) : (
                                      <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{cve.cwe_ids.join(', ') || 'N/A'}</p>
                                    )}
                                  </div>
                                </div>
                                <div>
                                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>影響を受ける構成（CPE）</span>
                                  <div style={{ maxHeight: '100px', overflowY: 'auto', marginTop: '4px', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                                    {cve.cpe_names.map((cpe, i) => (
                                      <div key={i} className="font-mono" style={{ whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }} title={cpe}>
                                        {cpe}
                                      </div>
                                    ))}
                                    {cve.cpe_names.length === 0 && 'N/A'}
                                  </div>
                                </div>
                              </div>

                              {cve.is_kev && cve.kev_info && (
                                <div style={{ border: '1px solid rgba(244, 63, 94, 0.2)', background: 'rgba(244, 63, 94, 0.02)', padding: '20px', borderRadius: '8px', marginBottom: '20px' }}>
                                  <h5 style={{ color: 'var(--accent-rose)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                                    <Icons.AlertTriangle /> CISA KEV (既知の悪用された脆弱性) 情報
                                  </h5>
                                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '0.875rem' }}>
                                    <p><strong>対象製品:</strong> {cve.kev_info.product}</p>
                                    <p><strong>悪用手法名:</strong> {cve.kev_info.vulnerablity_name}</p>
                                    <p><strong>カタログ追加日:</strong> {formatDateOnly(cve.kev_info.added_date)}</p>
                                    <p><strong>ランサムウェア悪用:</strong> {cve.kev_info.known_ransomware_campaign_use}</p>
                                  </div>
                                  <p style={{ marginTop: '12px', fontSize: '0.875rem' }}><strong>必要な対応策:</strong> {cve.kev_info.required_action}</p>
                                </div>
                              )}

                              {cve.advisories && cve.advisories.length > 0 && (
                                <div style={{ background: 'rgba(59, 130, 246, 0.02)', border: '1px solid rgba(59, 130, 246, 0.15)', padding: '20px', borderRadius: '8px' }}>
                                  <h5 style={{ color: 'var(--accent-blue)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
                                    <Icons.Shield /> GitHub セキュリティアドバイザリ (GHSA)
                                  </h5>
                                  {cve.advisories.map((adv, idx) => (
                                    <div key={idx} style={{ borderBottom: idx < cve.advisories.length - 1 ? '1px solid var(--border)' : 'none', paddingBottom: idx < cve.advisories.length - 1 ? '12px' : 0, paddingTop: idx > 0 ? '12px' : 0 }}>
                                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                                        <span className="font-mono" style={{ fontWeight: 600 }}>{adv.ghsa_id}</span>
                                        <span className="badge badge-blue">{adv.severity}</span>
                                      </div>
                                      <p style={{ fontSize: '0.9rem', marginBottom: '8px' }}>{adv.summary}</p>
                                      <div style={{ display: 'flex', gap: '16px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        <span>パッケージ: <code className="font-mono">{adv.affected_package}</code></span>
                                        {adv.patched_versions && <span>修正バージョン: <code className="font-mono">{adv.patched_versions}</code></span>}
                                        <a href={adv.url} target="_blank" rel="noopener noreferrer">詳細 <Icons.ExternalLink /></a>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // 3. arXiv Tab Render
  const renderArxiv = () => {
    const filteredPapers = data.arxiv.filter(paper =>
      paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      paper.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      paper.authors.some(author => author.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
      <div className="fade-in">
        <div className="search-container">
          <input
            type="text"
            placeholder="論文タイトル、要約、著者から検索..."
            className="search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="card-grid">
          {filteredPapers.length === 0 ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              条件に一致する論文が見つかりませんでした。
            </div>
          ) : (
            filteredPapers.map((paper) => (
              <div key={paper.arxiv_id} className="glass-panel card">
                <div className="card-header">
                  <span className="badge badge-purple" style={{ fontSize: '0.75rem' }}>arXiv: {paper.arxiv_id}</span>
                  <span className="sync-time" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Icons.Calendar /> {formatDateOnly(paper.published_at)}
                  </span>
                </div>
                <h3 className="card-title">{paper.title}</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>著者: {paper.authors.join(', ')}</p>

                <p className="card-summary">{paper.summary}</p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
                  {paper.categories.map((cat, i) => (
                    <span key={i} className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>{cat}</span>
                  ))}
                  {paper.owasp_mapping && paper.owasp_mapping.map((map, i) => (
                    <span key={i} className="badge badge-amber" style={{ fontSize: '0.7rem' }}>{map}</span>
                  ))}
                  {paper.mitre_mapping && paper.mitre_mapping.map((map, i) => (
                    <span key={i} className="badge badge-rose" style={{ fontSize: '0.7rem' }}>{map}</span>
                  ))}
                </div>

                <div className="card-footer">
                  <span>重要度スコア: <strong style={{ color: 'var(--accent-cyan)' }}>{paper.importance_score ? paper.importance_score.toFixed(2) : 'N/A'}</strong></span>
                  <div style={{ display: 'flex', gap: '16px' }}>
                    <a href={paper.abs_url} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      Abstract <Icons.ExternalLink />
                    </a>
                    <a href={paper.pdf_url} target="_blank" rel="noopener noreferrer" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      PDF <Icons.ExternalLink />
                    </a>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  // 4. Blogs & News Tab Render
  const renderBlogsAndNews = () => {
    const filteredArticles = data.rss_articles.filter(art =>
      art.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (art.summary && art.summary.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    return (
      <div className="fade-in">
        <div className="search-container">
          <input
            type="text"
            placeholder="記事タイトル、要約から検索..."
            className="search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="card-grid">
          {filteredArticles.length === 0 ? (
            <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              条件に一致する記事が見つかりませんでした。
            </div>
          ) : (
            filteredArticles.map((art) => (
              <div key={art.article_id} className="glass-panel card">
                <div className="card-header">
                  <span className="badge badge-blue">{art.source_name || 'RSS 記事'}</span>
                  <span className="sync-time" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Icons.Calendar /> {formatDateOnly(art.published_at)}
                  </span>
                </div>
                <h3 className="card-title">
                  <a href={art.url} target="_blank" rel="noopener noreferrer">
                    {art.title} <Icons.ExternalLink />
                  </a>
                </h3>

                {art.summary && <p className="card-summary">{art.summary}</p>}

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '4px' }}>
                  {art.owasp_mapping && art.owasp_mapping.map((map, i) => (
                    <span key={i} className="badge badge-amber" style={{ fontSize: '0.7rem' }}>{map}</span>
                  ))}
                  {art.mitre_mapping && art.mitre_mapping.map((map, i) => (
                    <span key={i} className="badge badge-rose" style={{ fontSize: '0.7rem' }}>{map}</span>
                  ))}
                  {art.nist_mapping && art.nist_mapping.map((map, i) => (
                    <span key={i} className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>{map}</span>
                  ))}
                </div>

                <div className="card-footer" style={{ borderTop: 'none', paddingDirect: 0, paddingBottom: 0 }}>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>取得日時: {formatDateTime(art.fetched_at)}</span>
                  {art.importance_score && <span>重要度: <strong style={{ color: 'var(--accent-cyan)' }}>{art.importance_score.toFixed(2)}</strong></span>}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    );
  };

  // 5. Reference Data (MITRE ATLAS / NIST Playbook) Render
  const renderReference = () => {
    return (
      <div className="fade-in">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>

          {/* MITRE ATLAS */}
          <div className="glass-panel" style={{ padding: '30px' }}>
            <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Icons.Shield /> MITRE ATLAS (AIの攻撃戦術・手法)
            </h3>
            <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '10px' }}>
              {data.atlas.tactics.map((tactic) => {
                // Find techniques for this tactic
                const relatedTechs = data.atlas.techniques.filter(t => t.tactic_id === tactic.tactic_id);
                return (
                  <div key={tactic.tactic_id} style={{ borderBottom: '1px solid var(--border)', paddingBottom: '16px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                      <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-rose)' }}>{tactic.tactic_id}</span>
                      <strong style={{ fontSize: '0.975rem' }}>{tactic.name}</strong>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '8px' }}>{tactic.description}</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {relatedTechs.map(tech => (
                        <span key={tech.technique_id} className="badge badge-purple" style={{ fontSize: '0.675rem' }} title={tech.description}>
                          {tech.name}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* NIST AI RMF Playbook */}
          <div className="glass-panel" style={{ padding: '30px' }}>
            <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Icons.FileText /> NIST AI RMFプレイブック・コントロール
            </h3>
            <div style={{ maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', paddingRight: '10px' }}>
              {data.nist_controls.slice(0, 15).map((ctrl) => (
                <div key={ctrl.control_id} style={{ borderBottom: '1px solid var(--border)', paddingBottom: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                    <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>{ctrl.function}</span>
                    <span className="font-mono" style={{ fontWeight: 700 }}>{ctrl.control_id}</span>
                    <strong style={{ fontSize: '0.925rem' }}>{ctrl.category}</strong>
                  </div>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{ctrl.description}</p>
                </div>
              ))}
              {data.nist_controls.length > 15 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center', marginTop: '10px' }}>
                  (全 {data.nist_controls.length} 件の NIST コントロールのうち最初の 15 件を表示しています)
                </p>
              )}
            </div>
          </div>

        </div>
      </div>
    );
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="brand">
          <div className="brand-logo">S</div>
          <div>
            <div className="brand-title">AI MONITOR</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.1em' }}>AI向けセキュリティ</div>
          </div>
        </div>

        <ul className="nav-menu">
          <li
            className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => { setActiveTab('overview'); setSearchQuery(''); }}
          >
            <Icons.Overview />
            <span>概要</span>
          </li>
          <li
            className={`nav-item ${activeTab === 'vulnerabilities' ? 'active' : ''}`}
            onClick={() => { setActiveTab('vulnerabilities'); setSearchQuery(''); }}
          >
            <Icons.Bug />
            <span>脆弱性情報</span>
            {data.cves.length > 0 && (
              <span className="badge badge-rose" style={{ marginLeft: 'auto', padding: '2px 6px', fontSize: '0.65rem' }}>
                {data.cves.length}
              </span>
            )}
          </li>
          <li
            className={`nav-item ${activeTab === 'arxiv' ? 'active' : ''}`}
            onClick={() => { setActiveTab('arxiv'); setSearchQuery(''); }}
          >
            <Icons.BookOpen />
            <span>学術論文</span>
          </li>
          <li
            className={`nav-item ${activeTab === 'rss' ? 'active' : ''}`}
            onClick={() => { setActiveTab('rss'); setSearchQuery(''); }}
          >
            <Icons.Globe />
            <span>ニュース・ブログ</span>
          </li>
          <li
            className={`nav-item ${activeTab === 'reference' ? 'active' : ''}`}
            onClick={() => { setActiveTab('reference'); setSearchQuery(''); }}
          >
            <Icons.Shield />
            <span>フレームワーク</span>
          </li>
        </ul>

        <div className="sidebar-footer">
          <div className="sync-time">システム状態: 稼働中</div>
          <div className="sync-time" style={{ marginTop: '4px' }}>最終エクスポート: {formatDateTime(data.meta.generated_at)}</div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <div className="page-header">
          <div className="page-info">
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700 }}>
              {activeTab === 'overview' && 'システム概要'}
              {activeTab === 'vulnerabilities' && '脆弱性モニター'}
              {activeTab === 'arxiv' && 'AIセキュリティ研究論文'}
              {activeTab === 'rss' && '脅威インテリジェンス・ニュース'}
              {activeTab === 'reference' && 'セキュリティフレームワーク'}
            </h1>
            <p className="page-subtitle">
              {activeTab === 'overview' && 'AIシステムに関する脆弱性・脅威情報、学術論文、技術動向の統合ダッシュボード'}
              {activeTab === 'vulnerabilities' && 'NVD CVE、EPSSスコア、CISA KEV、アドバイザリに基づく脆弱性の相関監視'}
              {activeTab === 'arxiv' && 'arXiv から自動収集された最新のAIセキュリティ・脆弱性に関連する研究論文'}
              {activeTab === 'rss' && '主要なベンダーブログやセキュリティニュースメディアのRSSクローラーフィード'}
              {activeTab === 'reference' && 'NIST AI RMFプレイブックのコントロールおよび MITRE ATLAS 攻撃戦術のナレッジベース'}
            </p>
          </div>

          <span className="badge badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ width: '6px', height: '6px', background: '#34d399', borderRadius: '50%', display: 'inline-block', boxShadow: '0 0 8px #34d399' }}></span>
            監視アクティブ
          </span>
        </div>

        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'vulnerabilities' && renderVulnerabilities()}
        {activeTab === 'arxiv' && renderArxiv()}
        {activeTab === 'rss' && renderBlogsAndNews()}
        {activeTab === 'reference' && renderReference()}
      </div>
    </div>
  );
}
