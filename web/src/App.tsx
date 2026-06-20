import {
  ArrowUpRight,
  Bot,
  CheckCircle2,
  ChevronRight,
  Database,
  Download,
  FileText,
  Filter,
  LineChart,
  Link2,
  Languages,
  Search,
  ShieldCheck,
  Sparkles,
  Table2,
} from "lucide-react";
import { useMemo, useState } from "react";
import brandsData from "./data/brands.json";
import evidenceData from "./data/evidence.json";
import sectionsData from "./data/brief_sections.json";
import { AgentConsole } from "./components/AgentConsole";

type BrandProfile = {
  brand_id: string;
  name: string;
  category: string;
  market_position: string;
  price_signal: string;
  expansion_model: string;
  franchise_model: string;
  brand_narrative: string;
  risk_signal: string;
  matrix_x: number;
  matrix_y: number;
  evidence_count: number;
  confidence: number;
};

type EvidenceRow = {
  evidence_id: string;
  brand_id: string;
  lens: string;
  claim: string;
  source_title: string;
  source_url: string;
  source_type: string;
  source_date: string;
  excerpt: string;
  confidence: number;
  review_status: "reviewed" | "needs_review" | "rejected";
  notes: string;
};

type BriefSection = {
  section_id: string;
  title: string;
  summary: string;
  supporting_evidence_ids: string[];
  confidence: number;
};

const brands = brandsData as BrandProfile[];
const evidence = evidenceData as EvidenceRow[];
const briefSections = sectionsData as BriefSection[];

const lensLabels: Record<string, string> = {
  all: "全部信号",
  pricing: "价格",
  expansion: "扩张",
  franchise: "加盟",
  positioning: "定位",
  risk: "风险",
};

const sourceLabels: Record<string, string> = {
  annual_report: "年报",
  prospectus: "招股书",
  company_site: "公司来源",
  news: "新闻",
  industry_report: "行业报告",
  job_posting: "JD",
};

const categoryLabels: Record<string, string> = {
  coffee: "咖啡",
  tea: "茶饮",
};

const matrixOffsets: Record<string, { x: number; y: number }> = {
  cotti: { x: -10, y: -8 },
  luckin: { x: 12, y: 7 },
  guming: { x: -22, y: 2 },
  chapanda: { x: 24, y: -4 },
  mixue: { x: -10, y: 3 },
};

function formatPct(value: number) {
  return `${Math.round(value * 100)}%`;
}

function compactName(name: string) {
  return name
    .replace(" Coffee", "")
    .replace(" Bingcheng", "")
    .replace(" China", "");
}

function isChineseSource(row: EvidenceRow) {
  return /[\u4e00-\u9fff]/.test(row.source_title);
}

function sourceDomain(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return "source";
  }
}

function AppMetric({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: React.ReactNode;
}) {
  return (
    <section className="metric">
      <div className="metric-icon">{icon}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
        <span>{detail}</span>
      </div>
    </section>
  );
}

function StatusPill({ status }: { status: EvidenceRow["review_status"] }) {
  return (
    <span className={`status status-${status}`}>
      {status === "reviewed" ? "已复核" : "待复核"}
    </span>
  );
}

function App() {
  const [selectedBrandId, setSelectedBrandId] = useState(brands[0]?.brand_id ?? "");
  const [activeLens, setActiveLens] = useState("all");
  const [query, setQuery] = useState("");

  const selectedBrand = useMemo(
    () => brands.find((brand) => brand.brand_id === selectedBrandId) ?? brands[0],
    [selectedBrandId],
  );

  const filteredEvidence = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return evidence.filter((row) => {
      const lensMatch = activeLens === "all" || row.lens === activeLens;
      const brandMatch = row.brand_id === selectedBrand.brand_id;
      const queryMatch =
        !normalizedQuery ||
        `${row.claim} ${row.source_title} ${row.excerpt}`.toLowerCase().includes(normalizedQuery);
      return lensMatch && brandMatch && queryMatch;
    });
  }, [activeLens, query, selectedBrand.brand_id]);

  const activeSection =
    briefSections.find((section) => section.section_id === activeLens) ??
    briefSections.find((section) => section.section_id === "overview") ??
    briefSections[0];

  const reviewedRatio =
    evidence.filter((row) => row.review_status === "reviewed").length / Math.max(evidence.length, 1);
  const averageConfidence =
    brands.reduce((total, brand) => total + brand.confidence, 0) / Math.max(brands.length, 1);
  const sourceCount = new Set(evidence.map((row) => row.source_url)).size;
  const chineseSourceCount = evidence.filter(isChineseSource).length;
  const sourceMix = evidence.reduce<Record<string, number>>((acc, row) => {
    acc[row.source_type] = (acc[row.source_type] ?? 0) + 1;
    return acc;
  }, {});
  const selectedEvidenceIds = new Set(filteredEvidence.map((row) => row.evidence_id));

  return (
    <main className="app-shell">
      <aside className="rail" aria-label="MarketLens 导航">
        <div className="rail-mark">ML</div>
        <nav>
          <a href="#agent" aria-label="Agent 控制台">
            <Sparkles size={19} />
          </a>
          <a href="#matrix" aria-label="定位矩阵">
            <LineChart size={19} />
          </a>
          <a href="#evidence" aria-label="证据表">
            <Table2 size={19} />
          </a>
          <a href="#brief" aria-label="简报输出">
            <FileText size={19} />
          </a>
          <a href="#workflow" aria-label="AI 工作流">
            <Bot size={19} />
          </a>
        </nav>
      </aside>

      <section className="workspace">
        <AgentConsole />

        <header className="hero-panel">
          <div className="hero-copy">
            <p className="eyebrow">
              <Sparkles size={15} />
              面向新茶饮/连锁咖啡的 AI 竞品研究工作台
            </p>
            <h1>MarketLens AI</h1>
            <p className="hero-subtitle">
              把分散的公司公告、招股书、行业新闻和市场信号整理成可追溯证据表、
              品牌定位矩阵与适合实习面试展示的品牌运营简报。
            </p>
          </div>
          <div className="hero-actions">
            <a className="button ghost" href="/data/brief.html" target="_blank" rel="noreferrer">
              <FileText size={17} />
              打开简报
            </a>
            <a className="button primary" href="/data/evidence.json" target="_blank" rel="noreferrer">
              <Download size={17} />
              下载证据 JSON
            </a>
          </div>
        </header>

        <section className="metric-grid" aria-label="MarketLens 指标">
          <AppMetric
            label="覆盖品牌"
            value={String(brands.length)}
            detail="咖啡 + 茶饮连锁"
            icon={<Database size={18} />}
          />
          <AppMetric
            label="证据条目"
            value={String(evidence.length)}
            detail={`${sourceCount} 个唯一来源链接`}
            icon={<Link2 size={18} />}
          />
          <AppMetric
            label="复核占比"
            value={formatPct(reviewedRatio)}
            detail="低置信度条目会显式标记"
            icon={<ShieldCheck size={18} />}
          />
          <AppMetric
            label="中文来源"
            value={formatPct(chineseSourceCount / Math.max(evidence.length, 1))}
            detail={`${chineseSourceCount}/${evidence.length} 条证据来自中文来源或中文转述`}
            icon={<Languages size={18} />}
          />
          <AppMetric
            label="平均置信度"
            value={formatPct(averageConfidence)}
            detail="按来源质量加权"
            icon={<CheckCircle2 size={18} />}
          />
        </section>

        <section className="dashboard-grid">
          <section className="panel brand-panel">
            <div className="section-heading">
              <div>
                <p className="kicker">研究范围</p>
                <h2>品牌观察清单</h2>
              </div>
              <Filter size={18} />
            </div>
            <div className="brand-list">
              {brands.map((brand) => (
                <button
                  key={brand.brand_id}
                  className={`brand-button ${
                    brand.brand_id === selectedBrand.brand_id ? "is-active" : ""
                  }`}
                  onClick={() => setSelectedBrandId(brand.brand_id)}
                >
                  <span className="brand-name">{brand.name}</span>
                  <span className={`category ${brand.category}`}>
                    {categoryLabels[brand.category] ?? brand.category}
                  </span>
                  <span className="confidence-track">
                    <span style={{ width: `${brand.confidence * 100}%` }} />
                  </span>
                </button>
              ))}
            </div>
          </section>

          <section className="panel matrix-panel" id="matrix">
            <div className="section-heading">
              <div>
                <p className="kicker">定位矩阵</p>
                <h2>价格位置 x 扩张动能</h2>
              </div>
              <span className="panel-badge">{selectedBrand.evidence_count} 条证据</span>
            </div>
            <div className="matrix">
              <span className="axis-label axis-top">高端叙事</span>
              <span className="axis-label axis-bottom">性价比规模</span>
              <span className="axis-label axis-left">扩张更快</span>
              <span className="axis-label axis-right">品牌控制</span>
              {brands.map((brand) => (
                <button
                  key={brand.brand_id}
                  className={`matrix-dot ${brand.category} ${
                    brand.brand_id === selectedBrand.brand_id ? "is-active" : ""
                  }`}
                  style={{
                    left: `calc(${brand.matrix_x * 100}% + ${
                      matrixOffsets[brand.brand_id]?.x ?? 0
                    }px)`,
                    bottom: `calc(${brand.matrix_y * 100}% + ${
                      matrixOffsets[brand.brand_id]?.y ?? 0
                    }px)`,
                  }}
                  onClick={() => setSelectedBrandId(brand.brand_id)}
                  aria-label={`选择 ${brand.name}`}
                >
                  {compactName(brand.name)}
                </button>
              ))}
            </div>
          </section>

          <section className="panel profile-panel">
            <div className="section-heading">
              <div>
                <p className="kicker">当前品牌信号</p>
                <h2>{selectedBrand.name}</h2>
              </div>
              <span className={`category ${selectedBrand.category}`}>
                {categoryLabels[selectedBrand.category] ?? selectedBrand.category}
              </span>
            </div>
            <p className="profile-position">{selectedBrand.market_position}</p>
            <dl className="signal-list">
              <div>
                <dt>价格</dt>
                <dd>{selectedBrand.price_signal}</dd>
              </div>
              <div>
                <dt>扩张</dt>
                <dd>{selectedBrand.expansion_model}</dd>
              </div>
              <div>
                <dt>加盟</dt>
                <dd>{selectedBrand.franchise_model}</dd>
              </div>
              <div>
                <dt>风险</dt>
                <dd>{selectedBrand.risk_signal}</dd>
              </div>
            </dl>
          </section>

          <section className="panel brief-panel" id="brief">
            <div className="section-heading">
              <div>
                <p className="kicker">简报生成器</p>
                <h2>{activeSection?.title ?? "市场概览"}</h2>
              </div>
              <span className="panel-badge">
                {activeSection ? formatPct(activeSection.confidence) : "N/A"}
              </span>
            </div>
            <div className="lens-tabs" aria-label="证据维度">
              {Object.keys(lensLabels).map((lens) => (
                <button
                  key={lens}
                  className={activeLens === lens ? "is-active" : ""}
                  onClick={() => setActiveLens(lens)}
                >
                  {lensLabels[lens]}
                </button>
              ))}
            </div>
            <p className="brief-summary">{activeSection?.summary}</p>
            <div className="evidence-chip-row">
              {(activeSection?.supporting_evidence_ids ?? []).slice(0, 7).map((id) => (
                <span
                  className={selectedEvidenceIds.has(id) ? "evidence-chip is-live" : "evidence-chip"}
                  key={id}
                >
                  {id}
                </span>
              ))}
            </div>
          </section>

          <section className="panel workflow-panel" id="workflow">
            <div className="section-heading">
              <div>
                <p className="kicker">AI 工作流</p>
                <h2>从网页信号到面试作品</h2>
              </div>
              <Bot size={19} />
            </div>
            <ol className="workflow-list">
              {[
                ["收集", "把公告、公司页面、招股书和行业新闻纳入来源登记表。"],
                ["结构化", "将事实主张整理为证据行，标注维度、置信度和复核状态。"],
                ["综合", "生成品牌画像、定位矩阵坐标和分维度研究简报。"],
                ["包装", "输出可演示 Demo、研究简报、SOP、Prompt 和面试讲法。"],
              ].map(([title, body], index) => (
                <li key={title}>
                  <span className="step-number">{index + 1}</span>
                  <div>
                    <strong>{title}</strong>
                    <p>{body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        </section>

        <section className="panel evidence-panel" id="evidence">
          <div className="section-heading evidence-heading">
            <div>
              <p className="kicker">证据追踪</p>
              <h2>{selectedBrand.name} 背后的证据</h2>
            </div>
            <label className="search-box">
              <Search size={17} />
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="搜索主张、来源或摘录"
              />
            </label>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>维度</th>
                  <th>证据主张</th>
                  <th>来源</th>
                  <th>置信度</th>
                  <th>状态</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvidence.map((row) => (
                  <tr key={row.evidence_id}>
                    <td>
                      <span className="lens-tag">{lensLabels[row.lens]}</span>
                    </td>
                    <td>
                      <strong>{row.claim}</strong>
                      <p>{row.excerpt}</p>
                    </td>
                    <td>
                      <a href={row.source_url} target="_blank" rel="noreferrer">
                        {sourceLabels[row.source_type] ?? row.source_type}
                        <ArrowUpRight size={14} />
                      </a>
                      <span className={isChineseSource(row) ? "source-language" : "source-language muted"}>
                        {isChineseSource(row) ? "中文来源" : "英文来源"} · {sourceDomain(row.source_url)}
                      </span>
                      <span className="source-title">{row.source_title}</span>
                      <span>{row.source_date}</span>
                    </td>
                    <td>{formatPct(row.confidence)}</td>
                    <td>
                      <StatusPill status={row.review_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="source-strip" aria-label="Source type mix">
          {Object.entries(sourceMix).map(([sourceType, count]) => (
            <span key={sourceType}>
              <ChevronRight size={14} />
              {sourceLabels[sourceType] ?? sourceType}: {count}
            </span>
          ))}
        </section>
      </section>
    </main>
  );
}

export { App };
