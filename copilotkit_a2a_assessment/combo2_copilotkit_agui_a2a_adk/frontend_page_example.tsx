/**
 * Combo 2: Frontend Page with Shared State + Human-in-Loop + Plan Display
 *
 * This example shows how the frontend can:
 * 1. Share state with the orchestrator via useCoAgent
 * 2. Display plans created by the orchestrator for approval
 * 3. Use useCopilotAction for human-in-loop tool calls
 *
 * File: app/recipe/page.tsx (conceptual example)
 */

"use client";
import {
  CopilotKit,
  useCoAgent,
  useCopilotChat,
  useCopilotAction,
} from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import React, { useState, useEffect } from "react";
import { Role, TextMessage } from "@copilotkit/runtime-client-gql";
import "@copilotkit/react-ui/styles.css";

// ============================================
// Types
// ============================================

interface Ingredient {
  icon: string;
  name: string;
  amount: string;
}

interface Recipe {
  title: string;
  skill_level: string;
  cooking_time: string;
  special_preferences: string[];
  ingredients: Ingredient[];
  instructions: string[];
}

interface Plan {
  steps: string[];
  agents_to_use: string[];
  description: string;
  status: "pending_approval" | "approved" | "rejected";
}

interface AgentState {
  recipe: Recipe;
  plan: Plan | null;
}

// ============================================
// Main Page Component
// ============================================

export default function RecipePage() {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      showDevConsole={false}
      agent="orchestrator" // Maps to the orchestrator HttpAgent in the API route
    >
      <div className="min-h-screen w-full flex items-center justify-center">
        <RecipeWithPlan />
        <CopilotSidebar
          defaultOpen={true}
          labels={{
            title: "AI Recipe Orchestrator",
            initial:
              "I can create recipes using specialized AI agents. Try asking me to create a recipe!",
          }}
          clickOutsideToClose={false}
        />
      </div>
    </CopilotKit>
  );
}

// ============================================
// Recipe + Plan Component with Shared State
// ============================================

const INITIAL_STATE: AgentState = {
  recipe: {
    title: "Make Your Recipe",
    skill_level: "Intermediate",
    cooking_time: "30 min",
    special_preferences: [],
    ingredients: [
      { icon: "🥕", name: "Carrots", amount: "3 large" },
    ],
    instructions: ["Preheat oven to 350°F"],
  },
  plan: null,
};

function RecipeWithPlan() {
  // Shared state with the orchestrator agent
  const { state: agentState, setState: setAgentState } =
    useCoAgent<AgentState>({
      name: "orchestrator",
      initialState: INITIAL_STATE,
    });

  const { appendMessage, isLoading } = useCopilotChat();
  const [recipe, setRecipe] = useState(INITIAL_STATE.recipe);
  const [plan, setPlan] = useState<Plan | null>(null);

  // ==========================================
  // Human-in-Loop: Register frontend action
  // The orchestrator can call this to get user approval
  // ==========================================
  useCopilotAction({
    name: "approve_plan",
    description:
      "Show a plan to the user and wait for their approval before executing",
    parameters: [
      {
        name: "plan_description",
        type: "string",
        description: "Description of the plan",
      },
      {
        name: "steps",
        type: "object[]",
        description: "Array of plan steps",
      },
    ],
    handler: async ({ plan_description, steps }) => {
      // This renders in the chat as an interactive component
      // User can approve or reject
      return {
        approved: true, // In real implementation, wait for user interaction
        feedback: "Looks good, proceed!",
      };
    },
  });

  // ==========================================
  // Sync agent state → local state
  // ==========================================
  useEffect(() => {
    if (agentState?.recipe) {
      setRecipe(agentState.recipe);
    }
    if (agentState?.plan !== undefined) {
      setPlan(agentState.plan);
    }
  }, [JSON.stringify(agentState)]);

  // ==========================================
  // Handle plan approval from UI
  // ==========================================
  const handleApprovePlan = () => {
    if (plan) {
      const updatedPlan = { ...plan, status: "approved" as const };
      setPlan(updatedPlan);
      setAgentState({
        ...agentState,
        plan: updatedPlan,
      });
      // Send a message to trigger the agent to proceed
      appendMessage(
        new TextMessage({
          content: "Plan approved. Please proceed.",
          role: Role.User,
        })
      );
    }
  };

  const handleRejectPlan = () => {
    if (plan) {
      const updatedPlan = { ...plan, status: "rejected" as const };
      setPlan(updatedPlan);
      setAgentState({
        ...agentState,
        plan: updatedPlan,
      });
      appendMessage(
        new TextMessage({
          content: "Plan rejected. Please suggest alternatives.",
          role: Role.User,
        })
      );
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6">
      {/* Plan Approval UI */}
      {plan && plan.status === "pending_approval" && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-bold text-lg mb-2">Execution Plan</h3>
          <p className="text-gray-600 mb-3">{plan.description}</p>
          <ol className="list-decimal list-inside mb-3">
            {plan.steps.map((step, i) => (
              <li key={i} className="mb-1">{step}</li>
            ))}
          </ol>
          <p className="text-sm text-gray-500 mb-3">
            Agents: {plan.agents_to_use.join(", ")}
          </p>
          <div className="flex gap-3">
            <button
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              onClick={handleApprovePlan}
            >
              Approve
            </button>
            <button
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              onClick={handleRejectPlan}
            >
              Reject
            </button>
          </div>
        </div>
      )}

      {/* Recipe Card */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">{recipe.title}</h2>
        <div className="flex gap-4 mb-4 text-sm text-gray-500">
          <span>🕒 {recipe.cooking_time}</span>
          <span>🏆 {recipe.skill_level}</span>
        </div>

        {/* Ingredients */}
        <h3 className="font-bold text-lg mb-2">Ingredients</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {recipe.ingredients.map((ing, i) => (
            <div key={i} className="flex items-center gap-2 bg-gray-50 rounded-lg p-2">
              <span>{ing.icon}</span>
              <div>
                <div className="font-medium text-sm">{ing.name}</div>
                <div className="text-xs text-gray-500">{ing.amount}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Instructions */}
        <h3 className="font-bold text-lg mb-2">Instructions</h3>
        <ol className="list-decimal list-inside">
          {recipe.instructions.map((inst, i) => (
            <li key={i} className="mb-1">{inst}</li>
          ))}
        </ol>

        {/* Improve Button */}
        <div className="mt-6 text-center">
          <button
            className={`px-6 py-3 rounded-full text-white font-semibold ${
              isLoading ? "bg-gray-400" : "bg-orange-500 hover:bg-orange-600"
            }`}
            disabled={isLoading}
            onClick={() => {
              if (!isLoading) {
                appendMessage(
                  new TextMessage({
                    content: "Improve this recipe using your specialized agents",
                    role: Role.User,
                  })
                );
              }
            }}
          >
            {isLoading ? "Working..." : "Improve with AI Agents"}
          </button>
        </div>
      </div>
    </div>
  );
}
