// ------------------------------------------------------------------
// S ce na ri oL oa dR eq ue st
// ------------------------------------------------------------------

import type { AIScenarioMode } from "./aiScenarioMode";

export type ScenarioLoadRequest = {
    source: "file";
    content: string;
} | {
    source: "ai";
    content: AIScenarioMode;
};