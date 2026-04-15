import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import type { AnyAgentTool, OpenClawPluginApi } from "openclaw/plugin-sdk";
import { jsonResult } from "openclaw/plugin-sdk";

const execFileAsync = promisify(execFile);
const PLUGIN_DIR = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_TIMEOUT_MS = 120000;

type JsonObject = Record<string, unknown>;
type ToolContextConfig = {
  aitpCommand?: string;
  workspaceRoot?: string;
  kernelRoot?: string;
  timeoutMs?: number;
};

const pluginConfigSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    aitpCommand: { type: "string" },
    workspaceRoot: { type: "string" },
    kernelRoot: { type: "string" },
    timeoutMs: {
      type: "integer",
      minimum: 1000,
      maximum: 600000,
      default: DEFAULT_TIMEOUT_MS,
    },
  },
} as const;

const doctorSchema = {
  type: "object",
  additionalProperties: false,
  properties: {},
} as const;

const stateSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic_slug"],
  properties: {
    topic_slug: { type: "string", minLength: 1, maxLength: 200 },
  },
} as const;

const auditSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic_slug"],
  properties: {
    topic_slug: { type: "string", minLength: 1, maxLength: 200 },
    phase: {
      anyOf: [{ enum: ["entry", "exit"] }, { type: "null" }],
      default: "exit",
    },
  },
} as const;

const decisionsSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic_slug"],
  properties: {
    topic_slug: { type: "string", minLength: 1, maxLength: 200 },
    pending_only: {
      anyOf: [{ type: "boolean" }, { type: "null" }],
      default: true,
    },
  },
} as const;

const resolveDecisionSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic_slug", "decision_id", "option"],
  properties: {
    topic_slug: { type: "string", minLength: 1, maxLength: 200 },
    decision_id: { type: "string", minLength: 1, maxLength: 200 },
    option: {
      type: "integer",
      minimum: 0,
      maximum: 32,
    },
    comment: {
      anyOf: [{ type: "string", minLength: 1, maxLength: 4000 }, { type: "null" }],
      default: null,
    },
    resolved_by: {
      anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }],
      default: "human",
    },
  },
} as const;

const resolveCheckpointSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic_slug", "option"],
  properties: {
    topic_slug: { type: "string", minLength: 1, maxLength: 200 },
    option: {
      type: "integer",
      minimum: 0,
      maximum: 32,
    },
    comment: {
      anyOf: [{ type: "string", minLength: 1, maxLength: 4000 }, { type: "null" }],
      default: null,
    },
    resolved_by: {
      anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }],
      default: "human",
    },
  },
} as const;

const interactionSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic_slug"],
  properties: {
    topic_slug: { type: "string", minLength: 1, maxLength: 200 },
  },
} as const;

const bootstrapSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic"],
  properties: {
    topic: { type: "string", minLength: 1, maxLength: 400 },
    topic_slug: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: null },
    statement: { anyOf: [{ type: "string", minLength: 1, maxLength: 4000 }, { type: "null" }], default: null },
    run_id: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: null },
    control_note: { anyOf: [{ type: "string", minLength: 1, maxLength: 2000 }, { type: "null" }], default: null },
    human_request: { anyOf: [{ type: "string", minLength: 1, maxLength: 4000 }, { type: "null" }], default: null },
    updated_by: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: "openclaw-plugin" },
    arxiv_ids: {
      anyOf: [{ type: "array", items: { type: "string", minLength: 1, maxLength: 200 }, maxItems: 20 }, { type: "null" }],
      default: [],
    },
    local_note_paths: {
      anyOf: [{ type: "array", items: { type: "string", minLength: 1, maxLength: 4000 }, maxItems: 20 }, { type: "null" }],
      default: [],
    },
    skill_queries: {
      anyOf: [{ type: "array", items: { type: "string", minLength: 1, maxLength: 1000 }, maxItems: 20 }, { type: "null" }],
      default: [],
    },
  },
} as const;

const resumeSchema = {
  type: "object",
  additionalProperties: false,
  required: ["topic_slug"],
  properties: {
    topic_slug: { type: "string", minLength: 1, maxLength: 200 },
    run_id: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: null },
    control_note: { anyOf: [{ type: "string", minLength: 1, maxLength: 2000 }, { type: "null" }], default: null },
    human_request: { anyOf: [{ type: "string", minLength: 1, maxLength: 4000 }, { type: "null" }], default: null },
    updated_by: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: "openclaw-plugin" },
    arxiv_ids: {
      anyOf: [{ type: "array", items: { type: "string", minLength: 1, maxLength: 200 }, maxItems: 20 }, { type: "null" }],
      default: [],
    },
    local_note_paths: {
      anyOf: [{ type: "array", items: { type: "string", minLength: 1, maxLength: 4000 }, maxItems: 20 }, { type: "null" }],
      default: [],
    },
    skill_queries: {
      anyOf: [{ type: "array", items: { type: "string", minLength: 1, maxLength: 1000 }, maxItems: 20 }, { type: "null" }],
      default: [],
    },
  },
} as const;

const loopSchema = {
  type: "object",
  additionalProperties: false,
  properties: {
    topic: { anyOf: [{ type: "string", minLength: 1, maxLength: 400 }, { type: "null" }], default: null },
    topic_slug: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: null },
    statement: { anyOf: [{ type: "string", minLength: 1, maxLength: 4000 }, { type: "null" }], default: null },
    run_id: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: null },
    control_note: { anyOf: [{ type: "string", minLength: 1, maxLength: 2000 }, { type: "null" }], default: null },
    human_request: { anyOf: [{ type: "string", minLength: 1, maxLength: 4000 }, { type: "null" }], default: null },
    updated_by: { anyOf: [{ type: "string", minLength: 1, maxLength: 200 }, { type: "null" }], default: "openclaw-plugin" },
    skill_queries: {
      anyOf: [{ type: "array", items: { type: "string", minLength: 1, maxLength: 1000 }, maxItems: 20 }, { type: "null" }],
      default: [],
    },
    max_auto_steps: {
      anyOf: [{ type: "integer", minimum: 1, maximum: 16 }, { type: "null" }],
      default: 1,
    },
  },
} as const;

function parseJson(stdout: string): JsonObject {
  const text = stdout.trim();
  if (!text) return {};
  return JSON.parse(text) as JsonObject;
}

function uniqueStrings(values: unknown): string[] {
  if (!Array.isArray(values)) return [];
  const seen = new Set<string>();
  const rows: string[] = [];
  for (const value of values) {
    if (typeof value !== "string") continue;
    const trimmed = value.trim();
    if (!trimmed || seen.has(trimmed)) continue;
    seen.add(trimmed);
    rows.push(trimmed);
  }
  return rows;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asArrayOfRecords(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => !!item && typeof item === "object" && !Array.isArray(item))
    : [];
}

function buildInteractionPacket(statusEnvelope: JsonObject, decisionsEnvelope: JsonObject): JsonObject {
  const statusResult = asRecord(statusEnvelope.result);
  const decisionsResult = asRecord(decisionsEnvelope.result);
  const operatorCheckpoint = asRecord(statusResult.operator_checkpoint);
  const humanPosture = asRecord(statusResult.human_interaction_posture);
  const pendingDecisionPoints = asArrayOfRecords(decisionsResult.decision_points);
  const operatorCheckpointRequested = String(operatorCheckpoint.status ?? "") === "requested";

  let primaryInteraction: JsonObject = {
    kind: "none",
    summary: "No active human-choice surface is currently blocking the bounded loop.",
  };

  if (pendingDecisionPoints.length > 0) {
    const first = pendingDecisionPoints[0] ?? {};
    primaryInteraction = {
      kind: "decision_point",
      id: first.id ?? null,
      question: first.question ?? null,
      blocking: Boolean(first.blocking),
      options: first.options ?? [],
      default_option_index: first.default_option_index ?? null,
      resolve_with: "aitp_resolve_decision",
    };
  } else if (operatorCheckpointRequested) {
    primaryInteraction = {
      kind: "operator_checkpoint",
      id: operatorCheckpoint.checkpoint_id ?? null,
      checkpoint_kind: operatorCheckpoint.checkpoint_kind ?? null,
      question: operatorCheckpoint.question ?? null,
      required_response: operatorCheckpoint.required_response ?? null,
      options: operatorCheckpoint.options ?? [],
      default_option_index: operatorCheckpoint.default_option_index ?? null,
      response_channels: operatorCheckpoint.response_channels ?? [],
      evidence_refs: operatorCheckpoint.evidence_refs ?? [],
      resolve_with: "aitp_resolve_checkpoint",
    };
  }

  return {
    topic_slug: statusResult.topic_slug ?? null,
    requires_human_input_now:
      Boolean(humanPosture.requires_human_input_now) || pendingDecisionPoints.length > 0 || operatorCheckpointRequested,
    human_interaction_posture: humanPosture,
    pending_decision_points: pendingDecisionPoints,
    operator_checkpoint: operatorCheckpoint,
    primary_interaction: primaryInteraction,
    response_tools: {
      inspect_interaction: "aitp_interaction",
      list_decisions: "aitp_decisions",
      resolve_decision: "aitp_resolve_decision",
      resolve_checkpoint: "aitp_resolve_checkpoint",
    },
  };
}

function looksLikeWorkspaceRoot(candidate: string): boolean {
  return (
    existsSync(path.join(candidate, "AGENTS.md")) &&
    existsSync(path.join(candidate, "research", "knowledge-hub"))
  );
}

function findWorkspaceRoot(startPath: string): string | null {
  let current = path.resolve(startPath);
  while (true) {
    if (looksLikeWorkspaceRoot(current)) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return null;
    }
    current = parent;
  }
}

function resolveRuntimeConfig(config: ToolContextConfig | null | undefined): Required<ToolContextConfig> {
  const workspaceRoot =
    (typeof config?.workspaceRoot === "string" && config.workspaceRoot.trim()
      ? path.resolve(config.workspaceRoot)
      : findWorkspaceRoot(PLUGIN_DIR) ?? findWorkspaceRoot(process.cwd()) ?? process.cwd());
  const kernelRoot =
    (typeof config?.kernelRoot === "string" && config.kernelRoot.trim()
      ? path.resolve(config.kernelRoot)
      : path.join(workspaceRoot, "research", "knowledge-hub"));
  const aitpCommand =
    typeof config?.aitpCommand === "string" && config.aitpCommand.trim() ? config.aitpCommand.trim() : "aitp";
  const timeoutMs =
    typeof config?.timeoutMs === "number" && Number.isFinite(config.timeoutMs)
      ? Math.max(1000, Math.min(600000, Math.trunc(config.timeoutMs)))
      : DEFAULT_TIMEOUT_MS;
  return { aitpCommand, workspaceRoot, kernelRoot, timeoutMs };
}

async function runAitp(config: ToolContextConfig | null | undefined, subcommand: string, args: string[]): Promise<JsonObject> {
  const runtime = resolveRuntimeConfig(config);
  const argv = [
    "--kernel-root",
    runtime.kernelRoot,
    "--repo-root",
    runtime.workspaceRoot,
    subcommand,
    ...args,
    "--json",
  ];
  try {
    const { stdout, stderr } = await execFileAsync(runtime.aitpCommand, argv, {
      cwd: runtime.workspaceRoot,
      timeout: runtime.timeoutMs,
      maxBuffer: 8 * 1024 * 1024,
      env: process.env,
    });
    const payload = parseJson(stdout);
    return {
      workspace_root: runtime.workspaceRoot,
      kernel_root: runtime.kernelRoot,
      command: runtime.aitpCommand,
      argv,
      ...(stderr && stderr.trim() ? { warning: stderr.trim() } : {}),
      result: payload,
    };
  } catch (error) {
    const failure = error as {
      message?: string;
      code?: number | string;
      stdout?: string;
      stderr?: string;
      killed?: boolean;
      signal?: string;
    };
    const details: JsonObject = {
      workspace_root: runtime.workspaceRoot,
      kernel_root: runtime.kernelRoot,
      command: runtime.aitpCommand,
      argv,
      exit_code: failure.code ?? null,
      killed: failure.killed ?? false,
      signal: failure.signal ?? null,
      stdout: failure.stdout?.trim() ?? "",
      stderr: failure.stderr?.trim() ?? "",
    };
    const message = failure.stderr?.trim() || failure.stdout?.trim() || failure.message || "AITP command failed";
    throw new Error(`${message}\n${JSON.stringify(details, null, 2)}`);
  }
}

function buildTools(api: OpenClawPluginApi, config: ToolContextConfig | null | undefined): AnyAgentTool[] {
  return [
    {
      name: "aitp_doctor",
      label: "AITP Doctor",
      description: "Check the current AITP CLI/kernel wiring for this OpenClaw workspace.",
      parameters: doctorSchema,
      async execute() {
        return jsonResult(await runAitp(config, "doctor", []));
      },
    } as AnyAgentTool,
    {
      name: "aitp_state",
      label: "AITP State",
      description: "Read the current runtime state for one AITP topic.",
      parameters: stateSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        return jsonResult(await runAitp(config, "state", ["--topic-slug", String(params.topic_slug)]));
      },
    } as AnyAgentTool,
    {
      name: "aitp_interaction",
      label: "AITP Interaction",
      description: "Return the active human-interaction packet for one topic: question, options, defaults, and how to answer.",
      parameters: interactionSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const topicSlug = String(params.topic_slug);
        const statusEnvelope = await runAitp(config, "interaction", ["--topic-slug", topicSlug]);
        const decisionsEnvelope = await runAitp(config, "list-decisions", ["--topic-slug", topicSlug, "--pending-only"]);
        return jsonResult({
          workspace_root: statusEnvelope.workspace_root,
          kernel_root: statusEnvelope.kernel_root,
          command: statusEnvelope.command,
          result: buildInteractionPacket(
            {
              ...statusEnvelope,
              result: {
                ...(asRecord(statusEnvelope.result)),
                operator_checkpoint: asRecord(asRecord(statusEnvelope.result).operator_checkpoint),
                human_interaction_posture: asRecord(asRecord(statusEnvelope.result).human_interaction_posture),
              },
            },
            decisionsEnvelope,
          ),
        });
      },
    } as AnyAgentTool,
    {
      name: "aitp_audit",
      label: "AITP Audit",
      description: "Run the AITP conformance audit for a topic.",
      parameters: auditSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const args = ["--topic-slug", String(params.topic_slug)];
        if (typeof params.phase === "string" && params.phase) {
          args.push("--phase", params.phase);
        }
        return jsonResult(await runAitp(config, "audit", args));
      },
    } as AnyAgentTool,
    {
      name: "aitp_decisions",
      label: "AITP Decisions",
      description: "List active AITP decision points so the host can render a bounded human-choice surface.",
      parameters: decisionsSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const args = ["--topic-slug", String(params.topic_slug)];
        if (params.pending_only !== false) args.push("--pending-only");
        return jsonResult(await runAitp(config, "list-decisions", args));
      },
    } as AnyAgentTool,
    {
      name: "aitp_resolve_decision",
      label: "AITP Resolve Decision",
      description: "Resolve one AITP decision point after the human chooses an option.",
      parameters: resolveDecisionSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const args = [
          "--topic-slug",
          String(params.topic_slug),
          "--decision-id",
          String(params.decision_id),
          "--option",
          String(params.option),
        ];
        if (typeof params.comment === "string" && params.comment) args.push("--comment", params.comment);
        if (typeof params.resolved_by === "string" && params.resolved_by) args.push("--resolved-by", params.resolved_by);
        return jsonResult(await runAitp(config, "resolve-decision", args));
      },
    } as AnyAgentTool,
    {
      name: "aitp_resolve_checkpoint",
      label: "AITP Resolve Checkpoint",
      description: "Resolve the active AITP operator checkpoint after the human chooses an option.",
      parameters: resolveCheckpointSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const args = [
          "--topic-slug",
          String(params.topic_slug),
          "--option",
          String(params.option),
        ];
        if (typeof params.comment === "string" && params.comment) args.push("--comment", params.comment);
        if (typeof params.resolved_by === "string" && params.resolved_by) args.push("--resolved-by", params.resolved_by);
        return jsonResult(await runAitp(config, "resolve-checkpoint", args));
      },
    } as AnyAgentTool,
    {
      name: "aitp_bootstrap",
      label: "AITP Bootstrap",
      description: "Bootstrap a new AITP topic through the installed kernel.",
      parameters: bootstrapSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const args = ["--topic", String(params.topic)];
        if (typeof params.topic_slug === "string" && params.topic_slug) args.push("--topic-slug", params.topic_slug);
        if (typeof params.statement === "string" && params.statement) args.push("--statement", params.statement);
        if (typeof params.run_id === "string" && params.run_id) args.push("--run-id", params.run_id);
        if (typeof params.control_note === "string" && params.control_note) args.push("--control-note", params.control_note);
        if (typeof params.human_request === "string" && params.human_request) args.push("--human-request", params.human_request);
        if (typeof params.updated_by === "string" && params.updated_by) args.push("--updated-by", params.updated_by);
        for (const arxivId of uniqueStrings(params.arxiv_ids)) args.push("--arxiv-id", arxivId);
        for (const notePath of uniqueStrings(params.local_note_paths)) args.push("--local-note-path", notePath);
        for (const skillQuery of uniqueStrings(params.skill_queries)) args.push("--skill-query", skillQuery);
        return jsonResult(await runAitp(config, "bootstrap", args));
      },
    } as AnyAgentTool,
    {
      name: "aitp_resume",
      label: "AITP Resume",
      description: "Resume an existing AITP topic through the installed kernel.",
      parameters: resumeSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const args = ["--topic-slug", String(params.topic_slug)];
        if (typeof params.run_id === "string" && params.run_id) args.push("--run-id", params.run_id);
        if (typeof params.control_note === "string" && params.control_note) args.push("--control-note", params.control_note);
        if (typeof params.human_request === "string" && params.human_request) args.push("--human-request", params.human_request);
        if (typeof params.updated_by === "string" && params.updated_by) args.push("--updated-by", params.updated_by);
        for (const arxivId of uniqueStrings(params.arxiv_ids)) args.push("--arxiv-id", arxivId);
        for (const notePath of uniqueStrings(params.local_note_paths)) args.push("--local-note-path", notePath);
        for (const skillQuery of uniqueStrings(params.skill_queries)) args.push("--skill-query", skillQuery);
        return jsonResult(await runAitp(config, "resume", args));
      },
    } as AnyAgentTool,
    {
      name: "aitp_loop",
      label: "AITP Loop",
      description: "Advance one bounded AITP loop step from OpenClaw without dropping back to ad hoc browsing.",
      parameters: loopSchema,
      async execute(_toolCallId, rawParams) {
        const params = (rawParams ?? {}) as Record<string, unknown>;
        const args: string[] = [];
        if (typeof params.topic === "string" && params.topic) args.push("--topic", params.topic);
        if (typeof params.topic_slug === "string" && params.topic_slug) args.push("--topic-slug", params.topic_slug);
        if (typeof params.statement === "string" && params.statement) args.push("--statement", params.statement);
        if (typeof params.run_id === "string" && params.run_id) args.push("--run-id", params.run_id);
        if (typeof params.control_note === "string" && params.control_note) args.push("--control-note", params.control_note);
        if (typeof params.human_request === "string" && params.human_request) args.push("--human-request", params.human_request);
        if (typeof params.updated_by === "string" && params.updated_by) args.push("--updated-by", params.updated_by);
        if (typeof params.max_auto_steps === "number" && Number.isFinite(params.max_auto_steps)) {
          args.push("--max-auto-steps", String(Math.max(1, Math.min(16, Math.trunc(params.max_auto_steps)))));
        }
        for (const skillQuery of uniqueStrings(params.skill_queries)) args.push("--skill-query", skillQuery);
        return jsonResult(await runAitp(config, "loop", args));
      },
    } as AnyAgentTool,
  ];
}

const plugin = {
  id: "aitp-openclaw-runtime",
  name: "AITP OpenClaw Runtime",
  description: "Typed AITP kernel tools plus the bundled OpenClaw runtime skill.",
  configSchema: pluginConfigSchema,
  register(api: OpenClawPluginApi) {
    api.registerTool(
      (ctx) => buildTools(api, (ctx.config ?? {}) as ToolContextConfig),
      { names: ["aitp_doctor", "aitp_state", "aitp_interaction", "aitp_audit", "aitp_decisions", "aitp_resolve_decision", "aitp_resolve_checkpoint", "aitp_bootstrap", "aitp_resume", "aitp_loop"] },
    );
    api.logger.info?.("aitp-openclaw-runtime: Registered aitp_* tools");
  },
};

export default plugin;
