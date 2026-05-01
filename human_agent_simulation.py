"""
Human vs. ASTRA Agent Negotiation

Negotiate interactively against the ASTRA NegotiationAgent.
You play as the partner; the agent will make strategic offers in response.

Usage:
    python human_agent_simulation.py \\
        --engine-STR gpt-4o-mini \\
        --negotiation-type integrative \\
        --STR

Keywords (type anywhere in your message):
    ACCEPT-DEAL   - accept the agent's last offer
    WALK-AWAY     - leave without a deal
"""

import argparse
import logging
import os
from datetime import datetime

from agent import NegotiationAgent, PartnerAgent, ModeratorAgent
from utils import (
    load_txt_file,
    calculate_score,
    convert_item_cnts_partner,
    setup_logging,
    save_dict_to_json,
)
from agent_agent_simulation import parse_agent_args, setup_negotiation_scenario

TOTAL_UNITS = 3
CURRENT_TIME = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Human vs. ASTRA negotiation")
    parser.add_argument("--engine-STR", type=str, default="gpt-4o-mini",
                        help="LLM engine for ASTRA (gpt-4o-mini, gpt-4o, claude-…, gemini-…)")
    parser.add_argument("--negotiation-type", type=str, default="integrative",
                        choices=["integrative", "distributive", "mixed"],
                        help="integrative = complementary values, distributive = same values")
    parser.add_argument("--n_round", type=int, default=12, help="Maximum negotiation rounds")
    parser.add_argument("--STR", action="store_true",
                        help="Enable ASTRA strategic reasoning (recommended)")
    parser.add_argument("--save", default=f"h2a_results/h2a_{CURRENT_TIME}.json",
                        help="Path to save the session result")
    parser = parse_agent_args(parser)
    return parser.parse_args()


def _fill_defaults(args: argparse.Namespace) -> argparse.Namespace:
    """Add fields that NegotiationAgent expects but aren't in parse_agent_args."""
    args.engine = args.engine_STR
    args.engine_OSAD = args.engine_STR
    args.engine_partner = args.engine_STR
    args.partner_other_prompting = "base"
    args.partner_agent_personality = "base"
    args.preset_partner_priority = False
    return args


# ---------------------------------------------------------------------------
# Agent construction
# ---------------------------------------------------------------------------

def build_agents(args, agent_values, partner_values):
    system_instruction = load_txt_file("prompt/system_instruction.txt")
    moderator_instruction = load_txt_file("prompt/moderator_instruction.txt")

    negotiator = NegotiationAgent(
        agent_value_off_table=agent_values,
        system_instruction=system_instruction,
        agent_type="NegotiatorAgent",
        engine=args.engine_STR,
        args=args,
    )
    osad_agent = PartnerAgent(
        agent_value_off_table=partner_values,
        system_instruction=system_instruction,
        agent_type="OSAD_agent",
        engine=args.engine_STR,
    )
    negotiator.set_OSAD_agent(osad_agent)

    moderator = ModeratorAgent(
        agent_type="Moderator",
        engine=args.engine_STR,
        system_instruction=moderator_instruction,
        trace_n_history=4,
        verbose=False,
    )
    return negotiator, moderator


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def _print_separator(char="=", width=62):
    print(char * width)


def show_welcome(human_values: dict):
    _print_separator()
    print("  ASTRA Negotiation  —  Human vs. Agent")
    _print_separator()
    print()
    print("SCENARIO")
    print(f"  Split {TOTAL_UNITS} units each of food, water, and firewood")
    print("  between yourself and the agent.")
    print()
    print("YOUR PRIVATE VALUES  (points per unit — keep these secret!)")
    priority_label = {5: "high", 4: "middle", 3: "low"}
    for item, val in human_values.items():
        label = priority_label.get(val, str(val))
        print(f"  {item:<10}  {val} pts  [{label} priority]")
    print()
    print("COMMANDS")
    print("  ACCEPT-DEAL   accept the agent's last proposed offer")
    print("  WALK-AWAY     leave the negotiation without a deal")
    print("  (anything else is your counter-offer in natural language)")
    _print_separator("-", 62)
    print()


def _show_split(agent_share: dict, human_share: dict):
    """Print a one-line summary of who gets what."""
    print(f"    Agent gets → food:{agent_share['food']}  water:{agent_share['water']}  firewood:{agent_share['firewood']}")
    print(f"    You get    → food:{human_share['food']}  water:{human_share['water']}  firewood:{human_share['firewood']}")


def show_agent_offer(negotiator: NegotiationAgent):
    """Show the most recent offer from ASTRA in a readable split."""
    if not negotiator.offer_history:
        return
    agent_share = negotiator.offer_history[-1]
    human_share = convert_item_cnts_partner(agent_share, only_cnts=True)
    print("  [Proposed split]")
    _show_split(agent_share, human_share)
    print()


def show_final_result(label: str, agent_share: dict, agent_values: dict, human_values: dict):
    human_share = convert_item_cnts_partner(agent_share, only_cnts=True)
    agent_score = calculate_score(agent_share, agent_values)
    human_score = calculate_score(human_share, human_values)
    print()
    _print_separator()
    print("FINAL RESULT")
    print(f"  {label}")
    print()
    print("  Final split:")
    _show_split(agent_share, human_share)
    print(f"  Agent score : {agent_score}")
    print(f"  Your score  : {human_score}")
    _print_separator()
    print()
    return agent_score, human_score


# ---------------------------------------------------------------------------
# Negotiation loop
# ---------------------------------------------------------------------------

def run_negotiation(
    negotiator: NegotiationAgent,
    moderator: ModeratorAgent,
    agent_values: dict,
    human_values: dict,
    n_round: int,
) -> dict:

    negotiator.reset()

    outcome = {
        "agreement": "NO-AGREEMENT",
        "agent_score": 0,
        "human_score": 0,
        "num_rounds": 0,
    }

    # --- Opening: human "greets", ASTRA responds with first offer ---
    opening = "Hello! Let's start the negotiation!"
    print(f"[YOU  ]: {opening}\n")
    print("[AGENT]: ", end="", flush=True)
    agent_response = negotiator.respond(opening)
    print(agent_response)
    show_agent_offer(negotiator)

    # --- Main loop ---
    for round_idx in range(1, n_round + 1):

        # Time-pressure nudge from moderator two rounds before the end
        if round_idx == n_round - 2:
            mod_msg = moderator.moderate_conversation()
            print(f"[MODERATOR]: {mod_msg}\n")
            negotiator.add_utterance_to_dialogue_history(mod_msg)

        if round_idx == n_round - 1:
            negotiator.compromised_decision_before_end = True
            print("[SYSTEM]: This is the final round!\n")

        print(f"--- Round {round_idx}/{n_round} ---")
        human_input = input("[YOU  ]: ").strip()
        if not human_input:
            continue
        print()

        # --- Human ends the negotiation ---
        if "ACCEPT-DEAL" in human_input.upper():
            if not negotiator.offer_history:
                print("[SYSTEM]: No offer to accept yet. Please wait for the agent to make an offer.\n")
                continue
            agent_score, human_score = show_final_result(
                "You accepted the agent's offer.",
                negotiator.offer_history[-1],
                agent_values,
                human_values,
            )
            outcome = {
                "agreement": "AGREEMENT",
                "who_accepted": "human",
                "agent_score": agent_score,
                "human_score": human_score,
                "num_rounds": round_idx,
            }
            break

        if "WALK-AWAY" in human_input.upper():
            print("\n[SYSTEM]: You walked away. No deal reached.\n")
            outcome = {
                "agreement": "WALK-AWAY",
                "who_walked": "human",
                "agent_score": 0,
                "human_score": 0,
                "num_rounds": round_idx,
            }
            break

        # --- Agent responds ---
        print("[AGENT]: ", end="", flush=True)
        agent_response = negotiator.respond(human_input)
        print(agent_response)

        # Agent accepts the human's counter-offer
        if "ACCEPT-DEAL" in agent_response:
            if negotiator.partner_offer_history:
                # partner_offer_history stores what ASTRA receives from the human's offer
                agent_share = negotiator.partner_offer_history[-1]
            elif negotiator.offer_history:
                agent_share = negotiator.offer_history[-1]
            else:
                print("[SYSTEM]: Agreement reached (no offer data available).\n")
                outcome = {"agreement": "AGREEMENT", "who_accepted": "agent", "num_rounds": round_idx}
                break
            agent_score, human_score = show_final_result(
                "The agent accepted your offer.",
                agent_share,
                agent_values,
                human_values,
            )
            outcome = {
                "agreement": "AGREEMENT",
                "who_accepted": "agent",
                "agent_score": agent_score,
                "human_score": human_score,
                "num_rounds": round_idx,
            }
            break

        if "WALK-AWAY" in agent_response:
            print("\n[SYSTEM]: The agent walked away. No deal reached.\n")
            outcome = {
                "agreement": "WALK-AWAY",
                "who_walked": "agent",
                "agent_score": 0,
                "human_score": 0,
                "num_rounds": round_idx,
            }
            break

        # Show the new proposed split after the agent's response
        show_agent_offer(negotiator)

        # Moderator sanity check
        check_status = moderator.check_status(negotiator.dialog_history)
        if check_status == "ACCEPT-DEAL":
            print("[SYSTEM]: Moderator declares a deal!\n")
            outcome = {"agreement": "AGREEMENT (moderator)", "num_rounds": round_idx}
            break
        elif check_status == "WALK-AWAY" and "WALK-AWAY" in agent_response:
            print("[SYSTEM]: Moderator confirms walk-away.\n")
            outcome = {
                "agreement": "WALK-AWAY (moderator)",
                "agent_score": 0,
                "human_score": 0,
                "num_rounds": round_idx,
            }
            break

        if round_idx == n_round:
            print("[SYSTEM]: Maximum rounds reached. No agreement.\n")
            outcome["num_rounds"] = round_idx

    return outcome


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Suppress LLM API noise; the conversation is printed directly to stdout
    setup_logging(logging.WARNING)

    args = parse_args()
    args = _fill_defaults(args)
    args.api_key = os.environ.get("OPENAI_API_KEY")

    agent_values, human_values, human_values_str = setup_negotiation_scenario(args)

    show_welcome(human_values)

    negotiator, moderator = build_agents(args, agent_values, human_values)

    result = run_negotiation(negotiator, moderator, agent_values, human_values, args.n_round)

    print("Session result:", result)

    os.makedirs(os.path.dirname(args.save) or ".", exist_ok=True)
    save_dict_to_json(result, args.save)
    print(f"Saved to {args.save}")


if __name__ == "__main__":
    main()
