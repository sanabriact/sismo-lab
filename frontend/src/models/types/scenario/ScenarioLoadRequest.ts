import type { AIScenarioMode } from "./aiScenarioMode";

export type ScenarioLoadRequest = {
    source: "file";
    content: string;
} | {
    source: "ai";
    content: AIScenarioMode;
};