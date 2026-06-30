import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  Archive,
  CheckCircle2,
  CircleDot,
  Eye,
  FileText,
  GitPullRequest,
  Hammer,
  History,
  ListChecks,
  MonitorSmartphone,
  Send,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
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

type PrStatusSnapshot = {
  schema_version: string;
  captured_at: string;
  repository: string;
  pull_request: number;
  display_url: string;
  head_sha: string;
  base_branch: string;
  head_branch: string;
  mergeable: boolean | null;
  merge_state: string;
  merged: boolean;
  checks: {
    status: string;
    conclusion: string | null;
    total_count: number;
    failing_count: number;
    unknown_count: number;
    runs: Array<{ name: string; status: string; conclusion: string | null; url: string | null }>;
  };
  policy_decision: string;
  risk_note: string;
  rollback_note: string;
  linked_task: string | null;
  direction_item: string | null;
  artifact_path?: string;
  operator_verdict?: {
    status: string;
    summary: string;
    next_action: string;
  };
};

type DirectionItem = {
  title: string;
  priority: number;
  scope: string;
  desired_outcome: string;
  details: string;
  avoid: string[];
  status: string;
  source: string;
  created_at: string;
};

type DashboardState = {
  repos: Item[];
  blueprints: Item[];
  runs: Item[];
  prs: Item[];
  logs: Item[];
  artifacts: Item[];
  directions: DirectionItem[];
  watch_items: Item[];
  cycle_entries: Item[];
  completion: {
    ready: CompletionPr[];
    blocked: CompletionPr[];
    failed_checks: CompletionPr[];
    stale: CompletionPr[];
    recently_merged: CompletionPr[];
    latest_snapshots: PrStatusSnapshot[];
    next_action: string;
    mode: string;
  };
};

type MissionControlState = {
  executive_status: {
    status: string;
    summary: string;
    overall_score: number;
    open_pr_count: number;
    failed_check_count: number;
    last_shipper_run: string | null;
    last_agent_cycle: string | null;
    top_recommendation: string;
  };
  scorecard: {
    overall_score: number;
    last_evaluated: string;
    metrics: Array<{
      name: string;
      score: number;
      status: "critical" | "needs_work" | "stable" | "excellent";
      verdict: string;
      evidence: string[];
      blocking_issues: string[];
      next_action: string;
      last_evaluated: string;
    }>;
  };
  changes: Array<{
    type: "landed" | "open" | "blocked" | "skipped" | "closed" | "agent_note";
    title: string;
    reference: string | null;
    timestamp: string | null;
    verdict: string;
    risk: string;
    next_action: string;
  }>;
  shipper: {
    exists: boolean;
    log_file: string;
    last_run_at: string | null;
    merged_prs: number[];
    skipped_prs: Array<{ number: number; reason: string }>;
    conflicts: string[];
    failed_checks: string[];
    dependency_review_overrides: string[];
    final_merged_count: number;
    summary: string;
  };
  health: {
    overall_status: string;
    summary: string;
    failed_checks: string[];
    checks: Record<string, { ok: boolean; summary: string; details?: string; path?: string }>;
  };
  token_warning: {
    detected: boolean;
    summary: string;
    guidance_path: string;
  };
  cycle: {
    found: boolean;
    timestamp: string | null;
    path: string | null;
    summary: string;
  };
  agent_activity: {
    degraded: boolean;
    summary: string;
    agent_lanes: Array<{
      role: string;
      status: string;
      summary: string;
      evidence: string[];
      next_action: string;
    }>;
    quality_verdicts: Array<{
      title: string;
      status: string;
      verdict: string;
      evidence: Array<string | null>;
      timestamp: string | null;
    }>;
    recent_runs: Array<Record<string, unknown>>;
    recent_commits: Array<Record<string, unknown>>;
  };
  visual_evidence: {
    summary: string;
    next_action: string;
    items: Array<{
      title: string;
      path: string;
      url: string;
      kind: string;
      captured_at: string;
      verdict: string;
    }>;
    expected: Array<{ title: string; path: string; purpose: string }>;
  };
  operator_access: {
    generated_at: string;
    frontend_port: number;
    api_port: number;
    lan_ip: string;
    tailscale_ip: string | null;
    primary_phone_url: string;
    api_url: string;
    launch_command: string;
    status: string;
    note: string;
    urls: Array<{ label: string; url: string; network: string; use_for: string }>;
  };
  product_showcase: {
    generated_at: string;
    summary: string;
    next_product_goal: string;
    products: Array<{
      title: string;
      status: string;
      what_was_built: string;
      open_url: string | null;
      visual_proof: string | null;
      test_evidence: string[];
      quality: string;
      next_action: string;
    }>;
  };
  product_controls: {
    active_goal_count: number;
    active_goals: DirectionItem[];
    suggested_builds: Array<{
      title: string;
      details: string;
      priority: number;
      why: string;
      acceptance: string;
    }>;
    lowest_metrics: Array<{ name: string; score: number; status: string; next_action: string }>;
    operator_prompt: string;
  };
  project_guidance: {
    strategic_objective: string;
    next_best_deliverable: string;
    why_it_matters: string;
    agent_next_action: string;
    garrett_next_action: string;
    do_not_do: string[];
    deliverable_target: {
      next_deliverable: string;
      outcome: string;
      acceptance: string;
      lowest_metric: string;
    };
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
    latest_snapshots: [],
    next_action: "Poll open PRs",
    mode: "dry-run",
  },
};

const emptyMission: MissionControlState = {
  executive_status: {
    status: "Loading",
    summary: "Collecting local and GitHub status.",
    overall_score: 0,
    open_pr_count: 0,
    failed_check_count: 0,
    last_shipper_run: null,
    last_agent_cycle: null,
    top_recommendation: "Refresh Mission Control.",
  },
  scorecard: { overall_score: 0, last_evaluated: "", metrics: [] },
  changes: [],
  shipper: {
    exists: false,
    log_file: "",
    last_run_at: null,
    merged_prs: [],
    skipped_prs: [],
    conflicts: [],
    failed_checks: [],
    dependency_review_overrides: [],
    final_merged_count: 0,
    summary: "No shipper status loaded.",
  },
  health: { overall_status: "unknown", summary: "Health not loaded.", failed_checks: [], checks: {} },
  token_warning: { detected: false, summary: "No token warning loaded.", guidance_path: "" },
  cycle: { found: false, timestamp: null, path: null, summary: "No cycle summary loaded." },
  agent_activity: { degraded: false, summary: "No activity loaded.", agent_lanes: [], quality_verdicts: [], recent_runs: [], recent_commits: [] },
  visual_evidence: { summary: "No visual proof loaded.", next_action: "", items: [], expected: [] },
  operator_access: {
    generated_at: "",
    frontend_port: 5274,
    api_port: 8765,
    lan_ip: "127.0.0.1",
    tailscale_ip: null,
    primary_phone_url: "http://127.0.0.1:5274",
    api_url: "http://127.0.0.1:8765",
    launch_command: ".\\scripts\\rf.ps1 phone",
    status: "loading",
    note: "Loading phone access.",
    urls: [],
  },
  product_showcase: {
    generated_at: "",
    summary: "Loading product proof.",
    next_product_goal: "Add a product direction.",
    products: [],
  },
  product_controls: {
    active_goal_count: 0,
    active_goals: [],
    suggested_builds: [
      {
        title: "Build the product Garrett describes",
        details: "Turn Garrett's product idea into an agent direction with PRs, checks, artifacts, and visible progress.",
        priority: 95,
        why: "This is the main human control path.",
        acceptance: "A product direction appears in the queue and progress is visible in Mission Control.",
      },
      {
        title: "Improve agent visibility",
        details: "Show what each agent is doing, whether it is good, and the evidence behind the verdict.",
        priority: 92,
        why: "Garrett currently feels blind.",
        acceptance: "Agent lanes, quality verdicts, logs, PRs, and visual proof are visible without raw log digging.",
      },
    ],
    lowest_metrics: [],
    operator_prompt: "What product should the agents build next?",
  },
  project_guidance: {
    strategic_objective: "",
    next_best_deliverable: "",
    why_it_matters: "",
    agent_next_action: "",
    garrett_next_action: "",
    do_not_do: [],
    deliverable_target: { next_deliverable: "", outcome: "", acceptance: "", lowest_metric: "" },
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

function PhoneAccessPanel({ access }: { access: MissionControlState["operator_access"] }) {
  const urls = access.urls.length ? access.urls : [{ label: "This device", url: access.primary_phone_url, network: "local", use_for: "Open Mission Control." }];
  return (
    <section className="phone-access">
      <div>
        <span className="eyebrow">Open From iPhone</span>
        <h2>{access.primary_phone_url}</h2>
        <p>{access.note}</p>
        <pre className="command-snippet">{access.launch_command}</pre>
      </div>
      <div className="phone-url-grid">
        {urls.map((item) => (
          <a className="phone-url-card" href={item.url} target="_blank" rel="noreferrer" key={`${item.network}-${item.url}`}>
            <span>{item.label}</span>
            <strong>{item.url}</strong>
            <small>{item.use_for}</small>
          </a>
        ))}
      </div>
    </section>
  );
}

function ProductShowcasePanel({ showcase }: { showcase: MissionControlState["product_showcase"] }) {
  return (
    <div className="product-showcase">
      <div className="operator-verdict">
        <strong>{showcase.summary}</strong>
        <code>proof-led</code>
      </div>
      <div className="product-grid">
        {showcase.products.length ? showcase.products.map((product) => (
          <article className="product-card" key={product.title}>
            {product.visual_proof ? <img src={`${apiBase}${product.visual_proof}`} alt={`${product.title} proof`} /> : null}
            <div>
              <div className="product-card-top">
                <strong>{product.title}</strong>
                <code>{product.status}</code>
              </div>
              <span>{product.what_was_built}</span>
              <small>Quality: {product.quality}</small>
              <small>Tests: {product.test_evidence.slice(0, 2).join(" · ")}</small>
              <small>Next: {product.next_action}</small>
              {product.open_url ? <a className="inline-link" href={product.open_url}>Open</a> : null}
            </div>
          </article>
        )) : <div className="empty-panel">No product cards yet. Add a direction and let the next cycle attach tests, PRs, and screenshots.</div>}
      </div>
      <div className="next-product-goal">{showcase.next_product_goal}</div>
    </div>
  );
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

async function createDirectionFromSuggestion(
  suggestion: { title: string; details: string; priority: number; acceptance?: string },
  refresh: () => Promise<void>,
) {
  await fetch(`${apiBase}/api/directions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: suggestion.title,
      desired_outcome: suggestion.acceptance ?? suggestion.title,
      details: suggestion.details,
      priority: suggestion.priority,
      scope: "global",
    }),
  });
  await refresh();
}

function DirectionQueue({
  items,
  onStatusChange,
}: {
  items: DirectionItem[];
  onStatusChange: (item: DirectionItem, status: "active" | "paused" | "done") => Promise<void>;
}) {
  return (
    <div className="direction-list">
      {items.map((item) => {
        const isActive = item.status === "active";
        const isPaused = item.status === "paused";
        const isDone = item.status === "done";
        return (
          <article className="direction-item" key={`${item.created_at}-${item.scope}-${item.title}`}>
            <div className="priority">{item.priority}</div>
            <div>
              <strong>{item.title}</strong>
              <span>{item.scope} · {item.desired_outcome}</span>
              {item.details ? <small>{item.details}</small> : null}
              {item.avoid.length > 0 ? <small>Avoid: {item.avoid.join(", ")}</small> : null}
              <small>{item.source} · {new Date(item.created_at).toLocaleString()}</small>
            </div>
            <div className="direction-status-controls">
              <code>{item.status}</code>
              <div className="direction-actions" aria-label={`Direction controls for ${item.title}`}>
                <button type="button" disabled={isActive} onClick={() => onStatusChange(item, "active")}>Reactivate</button>
                <button type="button" disabled={isPaused} onClick={() => onStatusChange(item, "paused")}>Pause</button>
                <button type="button" disabled={isDone} onClick={() => onStatusChange(item, "done")}>Done</button>
              </div>
            </div>
          </article>
        );
      })}
    </div>
  );
}

function SnapshotList({ snapshots }: { snapshots: PrStatusSnapshot[] }) {
  const visible = snapshots.slice(0, 4);
  return (
    <div className="snapshot-list">
      {visible.length ? visible.map((snapshot) => {
        const failing = snapshot.checks.failing_count;
        const unknown = snapshot.checks.unknown_count;
        const fallbackStatus = snapshot.policy_decision === "eligible" ? "ready" : failing ? "failed" : unknown ? "watch" : snapshot.policy_decision;
        const verdict = snapshot.operator_verdict;
        const status = verdict?.status ?? fallbackStatus;
        return (
          <article className="snapshot-row" key={`${snapshot.pull_request}-${snapshot.head_sha}`}>
            <div>
              <strong>#{snapshot.pull_request} {snapshot.repository}</strong>
              <span>{snapshot.head_branch} → {snapshot.base_branch} · {snapshot.merge_state} · {snapshot.policy_decision}</span>
              {verdict ? <small>{verdict.summary}</small> : <small>{snapshot.risk_note}</small>}
              {verdict ? <small>Next: {verdict.next_action}</small> : null}
              <small>{snapshot.checks.total_count} checks · {failing} failing · {unknown} unknown</small>
              {snapshot.artifact_path ? <small>{snapshot.artifact_path}</small> : null}
            </div>
            <code>{status}</code>
          </article>
        );
      }) : <div className="empty-panel">No PR status snapshots yet. Run pr_monitor with --write-snapshots.</div>}
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
      <div>
        <h3>Latest PR status artifacts</h3>
        <SnapshotList snapshots={completion.latest_snapshots} />
      </div>
    </div>
  );
}

function ExecutiveStrip({ mission }: { mission: MissionControlState }) {
  const summary = mission.executive_status.summary.replace(/^Attention needed:\s*/i, "").replace(/^Healthy:\s*/i, "");
  const items = [
    ["Overall score", `${mission.executive_status.overall_score}/10`],
    ["Open PRs", mission.executive_status.open_pr_count],
    ["Failed checks", mission.executive_status.failed_check_count],
    ["Last shipper", mission.executive_status.last_shipper_run ?? "No run"],
    ["Last cycle", mission.executive_status.last_agent_cycle ?? "No cycle"],
  ];
  return (
    <section className={`mission-hero ${mission.executive_status.status.toLowerCase().replace(/\s+/g, "-")}`}>
      <div>
        <span className="eyebrow">Mission Control</span>
        <h1>{mission.executive_status.status}: {summary}</h1>
        <p>{mission.executive_status.top_recommendation}</p>
      </div>
      <div className="mission-strip">
        {items.map(([label, value]) => (
          <div className="mission-strip-item" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function BuildConsole({
  controls,
  onBuild,
}: {
  controls: MissionControlState["product_controls"];
  onBuild: (suggestion: { title: string; details: string; priority: number; acceptance?: string }) => Promise<void>;
}) {
  return (
    <section className="build-console">
      <div className="build-console-main">
        <span className="eyebrow">Build Console</span>
        <h2>{controls.operator_prompt}</h2>
        <p>Choose a deliverable and Repo Foundry will add it to the agent direction queue. Progress, PRs, checks, logs, and proof should appear back here.</p>
      </div>
      <div className="build-suggestions">
        {controls.suggested_builds.map((item) => (
          <article className="build-card" key={item.title}>
            <div>
              <strong>{item.title}</strong>
              <span>{item.why}</span>
              <small>Acceptance: {item.acceptance}</small>
            </div>
            <button type="button" onClick={() => onBuild(item)}>
              <Send size={15} />
              Build this
            </button>
          </article>
        ))}
      </div>
      <div className="control-bottom">
        <div>
          <span>Active goals</span>
          <strong>{controls.active_goal_count}</strong>
        </div>
        <div>
          <span>Lowest metrics</span>
          <strong>{controls.lowest_metrics.map((metric) => `${metric.name} ${metric.score}/10`).join(" · ") || "None"}</strong>
        </div>
      </div>
    </section>
  );
}

function ScorecardPanel({ scorecard }: { scorecard: MissionControlState["scorecard"] }) {
  return (
    <div className="scorecard-grid">
      {scorecard.metrics.map((metric) => (
        <article className={`scorecard-card ${metric.status}`} key={metric.name}>
          <div className="scorecard-top">
            <strong>{metric.name}</strong>
            <span>{metric.score}/10</span>
          </div>
          <code>{metric.status}</code>
          <p>{metric.verdict}</p>
          {metric.blocking_issues.length ? <small>Blocked by: {metric.blocking_issues.join(" ")}</small> : <small>Evidence: {metric.evidence.slice(0, 2).join(" · ")}</small>}
          <small>Next: {metric.next_action}</small>
        </article>
      ))}
    </div>
  );
}

function WhatChangedPanel({ items }: { items: MissionControlState["changes"] }) {
  return (
    <div className="change-list">
      {items.map((item, index) => (
        <article className={`change-row ${item.type}`} key={`${item.type}-${item.title}-${index}`}>
          <div>
            <strong>{item.title}</strong>
            <span>{item.verdict}</span>
            <small>{item.timestamp ?? "No timestamp"} · {item.reference ?? "local reference unavailable"}</small>
            <small>Next: {item.next_action}</small>
          </div>
          <code>{item.type}</code>
        </article>
      ))}
    </div>
  );
}

function AgentActivityPanel({ activity }: { activity: MissionControlState["agent_activity"] }) {
  return (
    <div className="agent-lanes">
      <div className="operator-verdict">
        <strong>{activity.summary}</strong>
        <code>{activity.degraded ? "degraded" : "live"}</code>
      </div>
      {activity.agent_lanes.map((lane) => (
        <article className="agent-lane" key={lane.role}>
          <div>
            <strong>{lane.role}</strong>
            <span>{lane.summary}</span>
            <small>Next: {lane.next_action}</small>
            {lane.evidence.length ? <small>Evidence: {lane.evidence.join(" · ")}</small> : null}
          </div>
          <code>{lane.status}</code>
        </article>
      ))}
    </div>
  );
}

function QualityVerdictsPanel({ activity }: { activity: MissionControlState["agent_activity"] }) {
  const visible = activity.quality_verdicts.slice(0, 8);
  return (
    <div className="quality-list">
      {visible.length ? visible.map((item, index) => (
        <article className="quality-row" key={`${item.title}-${index}`}>
          <div>
            <strong>{item.title}</strong>
            <span>{item.verdict}</span>
            <small>{item.timestamp ?? "No timestamp"} · {(item.evidence.filter(Boolean) as string[]).join(" · ") || "No link"}</small>
          </div>
          <code>{item.status}</code>
        </article>
      )) : <div className="empty-panel">No quality verdicts yet. Run the next agent cycle or GitHub check collection.</div>}
    </div>
  );
}

function VisualEvidencePanel({ evidence }: { evidence: MissionControlState["visual_evidence"] }) {
  return (
    <div className="visual-proof">
      <div className="operator-verdict">
        <strong>{evidence.summary}</strong>
        <code>{evidence.items.length ? "proof" : "missing"}</code>
      </div>
      {evidence.items.length ? (
        <div className="visual-grid">
          {evidence.items.map((item) => (
            <figure className="visual-card" key={item.path}>
              <img src={`${apiBase}${item.url}`} alt={item.title} />
              <figcaption>
                <strong>{item.title}</strong>
                <span>{item.verdict}</span>
                <small>{item.captured_at} · {item.path}</small>
              </figcaption>
            </figure>
          ))}
        </div>
      ) : (
        <div className="visual-empty">
          <strong>No screenshot proof yet.</strong>
          <span>{evidence.next_action}</span>
          {evidence.expected.map((item) => (
            <small key={item.path}>{item.title}: {item.path} · {item.purpose}</small>
          ))}
        </div>
      )}
    </div>
  );
}

function ShipperPanel({ shipper }: { shipper: MissionControlState["shipper"] }) {
  return (
    <div className="operator-panel">
      <div className="operator-verdict">
        <strong>{shipper.summary}</strong>
        <code>{shipper.last_run_at ?? "no-run"}</code>
      </div>
      <div className="mini-grid">
        <div><span>Merged last run</span><strong>{shipper.final_merged_count || shipper.merged_prs.length}</strong></div>
        <div><span>Skipped</span><strong>{shipper.skipped_prs.length}</strong></div>
        <div><span>Failed checks</span><strong>{shipper.failed_checks.length}</strong></div>
        <div><span>Conflicts</span><strong>{shipper.conflicts.length}</strong></div>
      </div>
      <small>{shipper.log_file}</small>
      <pre className="command-snippet">.\scripts\repo_foundry_pr_shipper.ps1</pre>
    </div>
  );
}

function HealthPanel({ health }: { health: MissionControlState["health"] }) {
  const checks = Object.entries(health.checks);
  return (
    <div className="health-grid">
      <div className="operator-verdict">
        <strong>{health.summary}</strong>
        <code>{health.overall_status}</code>
      </div>
      {checks.map(([name, check]) => (
        <div className={`health-check ${check.ok ? "ok" : "warn"}`} key={name}>
          <span>{name.replace(/_/g, " ")}</span>
          <strong>{check.ok ? "OK" : "Needs attention"}</strong>
          <small>{check.summary}</small>
        </div>
      ))}
    </div>
  );
}

function SafetyPanel({ warning }: { warning: MissionControlState["token_warning"] }) {
  return (
    <div className={`safety-card ${warning.detected ? "warn" : "ok"}`}>
      <AlertTriangle size={18} />
      <div>
        <strong>{warning.detected ? "Credential warning" : "Credential check"}</strong>
        <span>{warning.summary}</span>
        <small>{warning.guidance_path}</small>
      </div>
    </div>
  );
}

function ProjectGuidancePanel({ guidance }: { guidance: MissionControlState["project_guidance"] }) {
  return (
    <div className="guidance">
      <strong>{guidance.next_best_deliverable}</strong>
      <p>{guidance.strategic_objective}</p>
      <div className="guidance-target">
        <span>Outcome</span>
        <strong>{guidance.deliverable_target.outcome}</strong>
        <span>Acceptance</span>
        <strong>{guidance.deliverable_target.acceptance}</strong>
      </div>
      <small>Agents: {guidance.agent_next_action}</small>
      <small>Garrett: {guidance.garrett_next_action}</small>
      <small>Do not: {guidance.do_not_do.join(" · ")}</small>
    </div>
  );
}

function App() {
  const [state, setState] = useState<DashboardState>(emptyState);
  const [mission, setMission] = useState<MissionControlState>(emptyMission);
  const [cycleLog, setCycleLog] = useState("");
  const [plan, setPlan] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const [dashboard, log, reconcile, missionControl] = await Promise.all([
      fetch(`${apiBase}/api/dashboard`).then((r) => r.json()),
      fetch(`${apiBase}/api/cycle-log`).then((r) => r.json()),
      fetch(`${apiBase}/api/reconcile/example`).then((r) => r.json()),
      fetch(`${apiBase}/api/mission-control`).then((r) => r.json()),
    ]);
    setState(dashboard);
    setMission(missionControl);
    setCycleLog(log.content);
    setPlan(reconcile);
    setLoading(false);
  }

  async function updateDirectionStatus(item: DirectionItem, status: "active" | "paused" | "done") {
    await fetch(`${apiBase}/api/directions/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ created_at: item.created_at, status }),
    });
    await refresh();
  }

  async function buildSuggestedDirection(suggestion: { title: string; details: string; priority: number; acceptance?: string }) {
    await createDirectionFromSuggestion(suggestion, refresh);
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
            <h1>Mission Control</h1>
            <p>Autonomous repo automation with safe shipping, audit trails, and phone-friendly visibility.</p>
          </div>
          <button onClick={refresh} disabled={loading}>
            <RefreshCcw size={16} />
            Refresh
          </button>
        </header>

        <ExecutiveStrip mission={mission} />

        <PhoneAccessPanel access={mission.operator_access} />

        <BuildConsole controls={mission.product_controls} onBuild={buildSuggestedDirection} />

        <div className="metrics">
          {counts.map(([label, value]) => (
            <div className="metric" key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>

        <div className="mission-grid">
          <Panel title="10/10 Scorecard" icon={<ListChecks size={18} />}>
            <ScorecardPanel scorecard={mission.scorecard} />
          </Panel>
          <Panel title="What Changed" icon={<History size={18} />}>
            <WhatChangedPanel items={mission.changes} />
          </Panel>
          <Panel title="Agent Activity Lanes" icon={<Sparkles size={18} />}>
            <AgentActivityPanel activity={mission.agent_activity} />
          </Panel>
          <Panel title="Visual Proof" icon={<Eye size={18} />}>
            <VisualEvidencePanel evidence={mission.visual_evidence} />
          </Panel>
          <Panel title="Products Created" icon={<MonitorSmartphone size={18} />} className="panel-products">
            <ProductShowcasePanel showcase={mission.product_showcase} />
          </Panel>
          <Panel title="Quality Verdicts" icon={<CheckCircle2 size={18} />}>
            <QualityVerdictsPanel activity={mission.agent_activity} />
          </Panel>
          <Panel title="Local PR Shipper" icon={<Hammer size={18} />}>
            <ShipperPanel shipper={mission.shipper} />
          </Panel>
          <Panel title="Health Check" icon={<CheckCircle2 size={18} />}>
            <HealthPanel health={mission.health} />
          </Panel>
          <Panel title="Safety" icon={<ShieldCheck size={18} />}>
            <SafetyPanel warning={mission.token_warning} />
          </Panel>
          <Panel title="Project Guidance" icon={<FileText size={18} />}>
            <ProjectGuidancePanel guidance={mission.project_guidance} />
          </Panel>
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
            <DirectionQueue items={state.directions} onStatusChange={updateDirectionStatus} />
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
