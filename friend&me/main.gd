extends Control

enum GamePhase { WAITING, SELECTION, ANSWERING, GUESSING, REVELATION }

@onready var phases_container: Control = $Phases
@onready var phase_nodes: Dictionary = {
	GamePhase.WAITING: $Phases/Phase0_Lobby,
	GamePhase.SELECTION: $Phases/Phase1_Selection,
	GamePhase.ANSWERING: $Phases/Phase2_Answering,
	GamePhase.GUESSING: $Phases/Phase3_Guessing,
	GamePhase.REVELATION: $Phases/Phase4_Revelation
}

var current_phase: GamePhase = GamePhase.WAITING

func _ready() -> void:
	# Hide all phases first, then show the initial phase
	switch_phase(GamePhase.WAITING)

func switch_phase(new_phase: GamePhase) -> void:
	current_phase = new_phase
	for phase_key in phase_nodes.keys():
		phase_nodes[phase_key].visible = (phase_key == current_phase)
	
	print("Switched to phase: ", GamePhase.keys()[current_phase])

# Testing function, you can call this to cycle through phases
func debug_next_phase() -> void:
	var next_idx = (int(current_phase) + 1) % phase_nodes.size()
	switch_phase(next_idx as GamePhase)
