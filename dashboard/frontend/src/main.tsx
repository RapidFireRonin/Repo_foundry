import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  CircleDot,
  FileText,
  GitPullRequest,
  Hammer,
  History,
  ListChecks,
  RefreshCcw,
  ShieldCheck,
} from "lucide-react";
import "./styles.css";

type Item = {
  id: number;
  kind: string;
  title: string;
  status: string;
  payload: Record<string, unknown>;
  created_at: string;
};

type DashboardState = {
  repos: Item[];
  blueprints: Item[];
  runs: Item[];
  prs: Item[];
  logs: Item[];
  artifacts: Item[];
  directions: Array<{
    title: string;
    priority: number;
    scope: string;
    desired_outcome: string;
    avoid: string[];
    status: string;
  }>;
  watch_items: Item[];
  cycle_entries: Item[];
};

const emptyState: DashboardState = {
  repos: [],
  blueprints: [],
  runs: [],
  prs: [],
  logs: [],
  artifacts: [],
  directions: [],
  watch_items: [],
  cycle_entries: [],
};

const apiBase = "http://127.0.0.1:8765";

function StatusDot({ status }: { status: string }) {
  const tone = status.includes("blocked") || status.includes("failed") ? "bad" : status.includes("review") || status.includes("draft") ? "warn" : "good";
  return <span className={`status-dot ${tone}`} aria-label={status} />;
}

function Panel({
  title,
  icon,
  children,
  action,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div className="panel-title">
          {icon}
          <h2>{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function ItemTable({ items }: { items: Item[] }) {
  return (
    <div className="table">
      {items.map((item) => (
        <div className="row" key={item.id}>
          <div className="row-main">
            <StatusDot status={item.status} />
            <div>
              <strong>{item.title}</strong>
              <span>{Object.entries(item.payload).map(([key, value]) => `${key}: ${String(value)}`).join(" · ") || "No extra metadata"}</span>
            </div>
          </div>
          <code>{item.status}</code>
        </div>
      ))}
    </div>
  );
}

function WatchQueue({ items }: { items: Item[] }) {
  return (
    <div className="review-list">
      {items.map((item) => (
        <article className="review-item" key={item.id}>
          <AlertTriangle size={18} />
          <div>
            <strong>{item.title}</strong>
            <span>Autonomous action is visible here for monitoring and follow-up.</span>
          </div>
          <code>{String(item.payload.impact ?? "watch")}</code>
        </article>
      ))}
    </div>
  );
}

function Timeline({ items }: { items: Item[] }) {
  return (
    <div className="timeline">
      {items.map((item) => (
        <div className="timeline-row" key={item.id}>
          <CircleDot size={16} />
          <div>
            <strong>{item.title}</strong>
            <span>{String(item.payload.path ?? item.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function DirectionQueue({ items }: { items: DashboardState["directions"] }) {
  return (
    <div className="direction-list">
      {items.map((item) => (
        <article className="direction-item" key={`${item.scope}-${item.title}`}>
          <div className="priority">{item.priority}</div>
          <div>
            <strong>{item.title}</strong>
            <span>{item.scope} · {item.desired_outcome}</span>
            {item.avoid.length > 0 ? <small>Avoid: {item.avoid.join(", ")}</small> : null}
          </div>
          <code>{item.status}</code>
        </article>
      ))}
    </div>
  );
}

function App() {
  const [state, setState] = useState<DashboardState>(emptyState);
  const [cycleLog, setCycleLog] = useState("");
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const [dashboard, log, reconcile] = await Promise.all([
      fetch(`${apiBase}/api/dashboard`).then((r) => r.json()),
      fetch(`${apiBase}/api/cycle-log`).then((r) => r.json()),
      fetch(`${apiBase}/api/reconcile/example`).then((r) => r.json()),
    ]);
    setState(dashboard);
    setCycleLog(log.content);
    setPlan(reconcile);
    setLoading(false);
  }

  useEffect(() => {
    refresh().catch(() => setLoading(false));
  }, []);

  const counts = useMemo(
    () => [
      ["Repos", state.repos.length],
      ["Watch", state.watch_items.length],
      ["Directions", state.directions.length],
      ["PRs", state.prs.length],
    ],
    [state],
  );

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <ShieldCheck size={24} />
          <div>
            <strong>Repo Foundry</strong>
            <span>Local control plane</span>
          </div>
        </div>
        <nav>
          <a className="active"><ListChecks size={17} /> Dashboard</a>
          <a><FileText size={17} /> Blueprints</a>
          <a><GitPullRequest size={17} /> Pull Requests</a>
          <a><History size={17} /> Cycle Log</a>
          <a><Archive size={17} /> Artifacts</a>
        </nav>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h1>Operational Overview</h1>
            <p>Autonomous repo automation with dry-run plans, audit trails, and friendly visibility.</p>
          </div>
          <button onClick={refresh} disabled={loading}>
            <RefreshCcw size={16} />
            Refresh
          </button>
        </header>

        <div className="metrics">
          {counts.map(([label, value]) => (
            <div className="metric" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>

        <div className="grid">
          <Panel title="Managed Repos" icon={<ShieldCheck size={18} />}>
            <ItemTable items={state.repos} />
          </Panel>
          <Panel title="Blueprint Drift" icon={<FileText size={18} />}>
            <ItemTable items={state.blueprints} />
          </Panel>
          <Panel title="Agent Runs" icon={<Hammer size={18} />}>
            <ItemTable items={state.runs} />
          </Panel>
          <Panel title="Pull Requests" icon={<GitPullRequest size={18} />}>
            <ItemTable items={state.prs} />
          </Panel>
          <Panel title="Autonomous Watchlist" icon={<AlertTriangle size={18} />}>
            <WatchQueue items={state.watch_items} />
          </Panel>
          <Panel title="Human Direction Queue" icon={<ListChecks size={18} />}>
            <DirectionQueue items={state.directions} />
          </Panel>
          <Panel title="Hourly Cycle Timeline" icon={<History size={18} />}>
            <Timeline items={state.cycle_entries} />
          </Panel>
        </div>

        <div className="wide-grid">
          <Panel title="Reconcile Plan" icon={<ListChecks size={18} />} action={<span className="pill">dry-run</span>}>
            <pre>{JSON.stringify(plan, null, 2)}</pre>
          </Panel>
          <Panel title="Logs and Artifacts" icon={<Archive size={18} />}>
            <ItemTable items={[...state.logs, ...state.artifacts]} />
          </Panel>
          <Panel title="Readable Cycle Log" icon={<CheckCircle2 size={18} />}>
            <pre>{cycleLog || "Cycle log is ready for the next hourly append."}</pre>
          </Panel>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
