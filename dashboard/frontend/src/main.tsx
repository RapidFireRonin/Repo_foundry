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
  Send,
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
    details: string;
    avoid: string[];
    status: string;
    source: string;
    created_at: string;
  }>;
  watch_items: Item[];
  cycle_entries: Item[];
  completion: {
    ready: CompletionPr[];
    blocked: CompletionPr[];
    failed_checks: CompletionPr[];
    stale: CompletionPr[];
    recently_merged: CompletionPr[];
    next_action: string;
    mode: string;
  };
};

type CompletionPr = {
  number: number;
  title: string;
  url: string;
  branch: string;
  mergeable: string;
  check_status: string;
  failed_checks: string[];
  stale: boolean;
  superseded_by?: number | null;
  decision: { allowed?: boolean; risk?: string; reasons?: string[] };
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
  completion: {
    ready: [],
    blocked: [],
    failed_checks: [],
    stale: [],
    recently_merged: [],
    next_action: "Poll open PRs",
    mode: "dry-run",
  },
};

const apiBase =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8765"
    : `${window.location.protocol}//${window.location.hostname}:8765`;

function StatusDot({ status }: { status: string }) {
  const tone = status.includes("blocked") || status.includes("failed") ? "bad" : status.includes("review") || status.includes("draft") ? "warn" : "good";
  return <span className={`status-dot ${tone}`} aria-label={status} />;
}

function Panel({
  title,
  icon,
  children,
  action,
  className = "",
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`panel ${className}`}>
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

function DirectionComposer({ onCreated }: { onCreated: () => Promise<void> }) {
  const [title, setTitle] = useState("");
  const [details, setDetails] = useState("");
  const [priority, setPriority] = useState(80);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const cleanTitle = title.trim();
    if (!cleanTitle) return;
    setSubmitting(true);
    await fetch(`${apiBase}/api/directions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: cleanTitle,
        desired_outcome: cleanTitle,
        details: details.trim(),
        priority,
        scope: "global",
      }),
    });
    setTitle("");
    setDetails("");
    setPriority(80);
    await onCreated();
    setSubmitting(false);
  }

  return (
    <form className="direction-composer" onSubmit={submit}>
      <label>
        <span>Goal</span>
        <textarea
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Build X, focus on GitHub adapter, improve dashboard..."
          rows={3}
        />
      </label>
      <label>
        <span>Details</span>
        <input
          value={details}
          onChange={(event) => setDetails(event.target.value)}
          placeholder="Optional constraints, context, or desired finish line"
        />
      </label>
      <div className="composer-actions">
        <label>
          <span>Priority</span>
          <select value={priority} onChange={(event) => setPriority(Number(event.target.value))}>
            <option value={95}>Critical</option>
            <option value={80}>High</option>
            <option value={60}>Normal</option>
            <option value={35}>Later</option>
          </select>
        </label>
        <button type="submit" disabled={submitting || !title.trim()}>
          <Send size={16} />
          Direct Agents
        </button>
      </div>
    </form>
  );
}

function DirectionQueue({ items }: { items: DashboardState["directions"] }) {
  return (
    <div className="direction-list">
      {items.map((item) => (
        <article className="direction-item" key={`${item.created_at}-${item.scope}-${item.title}`}>
          <div className="priority">{item.priority}</div>
          <div>
            <strong>{item.title}</strong>
            <span>{item.scope} · {item.desired_outcome}</span>
            {item.details ? <small>{item.details}</small> : null}
            {item.avoid.length > 0 ? <small>Avoid: {item.avoid.join(", ")}</small> : null}
            <small>{item.source} · {new Date(item.created_at).toLocaleString()}</small>
          </div>
          <code>{item.status}</code>
        </article>
      ))}
    </div>
  );
}

function CompletionPanel({ completion }: { completion: DashboardState["completion"] }) {
  const rows = [
    ["Ready", completion.ready.length, "good"],
    ["Blocked", completion.blocked.length, "bad"],
    ["Failed", completion.failed_checks.length, "bad"],
    ["Stale", completion.stale.length, "warn"],
    ["Merged", completion.recently_merged.length, "good"],
  ];
  const visible = [...completion.ready, ...completion.blocked, ...completion.stale].slice(0, 5);
  return (
    <div className="completion-panel">
      <div className="completion-summary">
        {rows.map(([label, value, tone]) => (
          <div className={`completion-stat ${tone}`} key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="completion-next">
        <strong>{completion.next_action}</strong>
        <code>{completion.mode}</code>
      </div>
      <div className="completion-list">
        {visible.length ? visible.map((pr) => (
          <article className="completion-row" key={pr.number}>
            <div>
              <strong>#{pr.number} {pr.title}</strong>
              <span>{pr.branch} · {pr.mergeable} · {pr.decision.risk ?? "unknown risk"}</span>
              {pr.decision.reasons?.length ? <small>{pr.decision.reasons.join("; ")}</small> : null}
              {pr.failed_checks.length ? <small>Failed: {pr.failed_checks.join(", ")}</small> : null}
            </div>
            <code>{pr.decision.allowed ? "ready" : pr.check_status}</code>
          </article>
        )) : <div className="empty-panel">No polled PRs yet.</div>}
      </div>
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
          <Panel title="Autonomous Completion" icon={<CheckCircle2 size={18} />} className="panel-completion">
            <CompletionPanel completion={state.completion} />
          </Panel>
          <Panel title="Autonomous Watchlist" icon={<AlertTriangle size={18} />}>
            <WatchQueue items={state.watch_items} />
          </Panel>
          <Panel title="Direct the Agents" icon={<Send size={18} />} className="panel-direct">
            <DirectionComposer onCreated={refresh} />
          </Panel>
          <Panel title="Human Direction Queue" icon={<ListChecks size={18} />} className="panel-directions">
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
