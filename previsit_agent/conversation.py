# Minimal stub for ConversationManager for testing
class ConversationManager:
	def __init__(self, llm):
		self.llm = llm
		self.turn_count = 0
	def start_conversation(self):
		return "Welcome!"
	def process_turn(self, patient_input):
		self.turn_count += 1
		return f"Agent response to: {patient_input}"
	def get_conversation_summary(self):
		return {
			"turn_count": self.turn_count,
			"completion_percentage": 100,
			"collected_data": ["data1", "data2"]
		}
