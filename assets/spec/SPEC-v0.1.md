# Coding Agent Control Deck
**Product Specification v0.1 | MiraBox N3** (Gabriel's original spec, Oct 27, 2026, verbatim)

## 1. Product Goal

Turn the MiraBox N3 into a physical control center for coding agents.

The user can switch between coding tools, monitor active sessions, change models, control reasoning effort, and review usage limits without opening settings menus.

### Hardware

- **3 metal buttons:** Select the operating mode.
- **6 LCD buttons:** Show live information and perform actions.
- **1 main knob:** Controls the primary action in each mode.
- **2 small knobs:** Control secondary actions.
- **Knob clicks:** Provide additional actions.

The three metal buttons always select the same modes. Switching modes must not interrupt active agents.

## 2. Mode 1: Agents

**Metal button: Left**

Purpose: Open coding tools, switch between their windows, and quickly adjust the current model.

### LCD buttons

The six screens have fixed positions.

| Position | Coding agent |
|---|---|
| Top left | Claude Code |
| Top middle | Cursor |
| Top right | Codex |
| Bottom left | OpenCode |
| Bottom middle | Amp |
| Bottom right | Devin |

Each screen shows the agent logo and a small activity indicator.

A screen click focuses the agent's latest window or session. If the application is closed, the click launches it. It must not start a new task automatically.

### Knobs

| Control | Rotation | Click |
|---|---|---|
| Main knob | Switch between open coding agent windows | Switch back to the previous window |
| Left knob | Change the model in the active session | Restore the default model |
| Right knob | Change reasoning effort in the active session | Restore default effort |

### Behavior

- The main knob cycles only through registered coding agent windows, not every window on the computer.
- Changing the model or effort applies to the selected session, not every session in that application.
- The deck shows a temporary confirmation when a setting changes.
- Unsupported controls show "Not available" and leave the session unchanged.
- Changes to model or effort apply to the next model request, unless the agent supports updating the current request.

## 3. Mode 2: Sessions

**Metal button: Middle**

Purpose: Monitor work across all coding agents and quickly open sessions that need attention.

### LCD buttons

Each of the six screens represents one agent session.

A session screen shows:

1. **Agent identity:** A small logo identifying Claude Code, Cursor, Codex, or another tool.
2. **Agent status:** A colored indicator showing the current state.
3. **Context usage:** A circular progress indicator showing how much of the context window is used.
4. **Task title:** A short title with up to three words, such as "Fix login bug."

### Session states

| State | Meaning |
|---|---|
| Working | The agent is processing a request |
| Needs approval | A tool or action requires permission |
| Needs input | The agent is waiting for a user response |
| Idle | The session is ready for another request |
| Completed | The task has finished |
| Disconnected | Live status is unavailable |

The user must be able to distinguish a session that needs approval from one that has simply finished working.

The context circle must show context usage, not cumulative token consumption. If the context size is unknown, show an unknown indicator instead of an estimated percentage.

### LCD actions

Clicking a session opens that exact session and makes it the selected session for the other modes.

Clicking a session that needs approval opens its approval prompt. It does not approve the action.

### Knobs

| Control | Rotation | Click |
|---|---|---|
| Main knob | Browse older and newer sessions, six at a time | Jump to the next session needing attention, or return to the newest page |
| Left knob | Filter sessions by coding agent | Clear the agent filter |
| Right knob | Filter by status: All, Working, Needs You, Idle, Completed | Clear the status filter |

### Behavior

- Sessions are ordered by recent activity.
- Sessions that need attention are highlighted.
- Session positions remain stable while the user interacts with the deck.
- The context circle and status update without moving the session to a different button.
- More than six sessions are accessible with the main knob.
- The latest filters and page position are remembered when switching modes.
- Local and remote sessions appear together when their integrations are connected.

## 4. Mode 3: Models & Usage

**Metal button: Right**

Purpose: Select models, monitor limits, and change the selected session's execution settings.

### LCD buttons

Each screen represents a model available to the selected coding agent.

For example, the Codex model list could contain Astra, Sol, and other supported models.

Each screen shows:

1. **Model name:** A short model label.
2. **Short-window usage:** A small horizontal usage bar.
3. **Long-window usage:** A second usage bar, when available.
4. **Selection status:** Whether this is the current model.

The time labels must use the real limit windows reported by the provider. For example, a five-hour window must not be labeled as hourly usage.

If several models share the same quota, they must show that they use a shared pool. A quota must not be presented as model-specific unless the provider reports it that way.

Up to six favorite models are shown per coding agent. Favorites can be configured from the desktop application.

### LCD actions

Clicking a model sets it as the selected session's model.

- If the model is supported, the change is applied to the next request.
- If the model is unavailable, show why.
- If the agent cannot change models within an existing session, do not pretend the change succeeded.

### Knobs

| Control | Rotation | Click |
|---|---|---|
| Main knob | Change reasoning effort | Toggle Claude Code Ultracode, when supported |
| Left knob | Switch the selected coding agent | Return to the agent of the last selected session |
| Right knob | Choose a permission level | Apply the selected permission level |

### Reasoning effort

The available levels depend on the model and coding agent.

For example:

- Low
- Medium
- High
- Extra High
- Max

Only levels supported by the current model appear.

**Ultracode is a separate setting, not an effort level.** Pressing the main knob toggles Claude Code Ultracode when that feature is available. It leaves the selected effort level unchanged.

Other coding agents must use their own supported controls. Amp's Ultra mode, for example, is not the same feature and cannot be applied to an existing Amp thread.

### Permission levels

Use a small set of common permission labels:

| Level | Behavior |
|---|---|
| Read-only | No file changes or command execution |
| Ask | Request approval for actions that require it |
| Auto | Automatically allow actions permitted by the agent's safe policy |
| Full | Broader access, only when explicitly supported and confirmed |

The right knob previews a permission level. Clicking it applies the setting.

Full access requires an additional confirmation on the computer. The deck must never silently bypass security prompts.

## 5. Shared Behavior

### Selected session

All three modes use one selected session.

A session becomes selected when the user:

- Opens its session screen in Sessions mode.
- Focuses a known session in Agents mode.
- Switches to another coding agent in Models & Usage mode, which selects the last explicitly used session for that agent.

A model, effort, or permission change must always have a known target. If no session is selected, the action is disabled.

### Temporary screen feedback

Knob actions can show a temporary visual message.

Example:

1. Rotate the effort knob.
2. The display shows "HIGH EFFORT."
3. The new setting is applied, when supported.
4. After five seconds, the normal screens return.

Further rotation restarts the five-second timer.

The temporary display does not undo the setting change. It only hides the message.

LCD buttons must never execute hidden actions while a temporary display covers their normal labels. Temporary messages should use small overlays when possible.

### Live updates

- Session status updates automatically.
- Context usage updates when new usage data arrives.
- Usage limits refresh periodically.
- A disconnected integration shows its last known data as stale or unavailable.
- When an action fails, the deck shows a clear error instead of a success message.

### Safety rules

- Never apply changes to an unknown session.
- Never approve agent tool calls automatically through the session tiles.
- Never enable unrestricted permissions without confirmation.
- Never show estimated usage as measured usage.
- Never use keyboard shortcuts to simulate a successful model change without verifying the result.

## 6. Software Requirements

A local application runs on the connected computer and controls the N3 over USB.

It includes:

1. **Device controller:** Reads button and knob events, updates LCD images, and manages modes.
2. **Session manager:** Tracks sessions, selected session, application windows, and recent activity.
3. **Agent integrations:** Connect to Claude Code, Cursor, Codex, OpenCode, Amp, and Devin using supported APIs, hooks, or local processes.
4. **Usage manager:** Reads context usage, provider quotas, and reset times when available.
5. **Desktop configuration:** Manages accounts, model favorites, supported integrations, and permissions.

Each integration must declare which actions it supports. Unsupported functions are disabled rather than simulated.

## 7. Acceptance Tests

**Agents mode**

- Pressing Codex focuses its window.
- Rotating the main knob switches to another open coding window.
- Changing effort updates the correct session, or reports that the action is unsupported.

**Sessions mode**

- Six live sessions appear.
- A waiting session changes its status indicator without moving.
- Rotating the main knob reveals older sessions.
- Clicking a session opens the correct conversation.

**Models & Usage mode**

- Selecting another coding agent changes the model list.
- Clicking a supported model updates the selected session.
- The usage bars show the correct quota windows.
- Rotating the right knob does not change permissions until the knob is pressed.
- Ultracode can only be toggled where it is supported.

## 8. Initial Scope

**Version 1**

- Hardware input and LCD rendering
- Three persistent operating modes
- Window switching and application launching
- Unified session tracking
- Codex, OpenCode, and Claude Code integrations
- Basic usage monitoring and model controls
- Clear unsupported-state feedback

**Later versions**

- Deeper Cursor integration
- Amp and Devin session integrations
- More complete permission management
- Improved usage data coverage
- Custom model favorites and screen layouts

The product should remain useful when only some coding agents are connected.
