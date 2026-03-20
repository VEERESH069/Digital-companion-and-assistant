# Minimal stub for LLMService for testing
class LLMService:
	def chat(self, messages):
		# Return a fake response for testing
		return "Hello!"
	def extract_post_conversation(self, transcript, session_id, patient_id):
		# Return a fake summary dict for testing
		return {
			"clinical_summary": "Test summary.",
			"urgency_level": "MEDIUM",
			"recommended_specialist": "General Dentist",
			"red_flags": []
		}
