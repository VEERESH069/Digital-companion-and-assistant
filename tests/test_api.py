"""
Comprehensive API tests for Pre-Visit Voice Agent
Run with: pytest tests/test_api.py -v
"""

import json
import pytest
from datetime import datetime, timezone

from database import Database
from models import ConversationSession, ConversationMessage, ClinicalData


class TestHealthAndInfo:
    """Test health check and info endpoints"""
    
    def test_health_check(self, client):
        """Test GET /health"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'database' in data
        assert 'version' in data
    
    def test_api_info(self, client):
        """Test GET /api/info"""
        response = client.get('/api/info')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'service' in data
        assert 'version' in data
        assert 'endpoints' in data


class TestSessionManagement:
    """Test session creation and management endpoints"""
    
    def test_create_session_success(self, client, sample_patient_id):
        """Test POST /api/sessions - Success"""
        response = client.post('/api/sessions', json={
            'patient_id': sample_patient_id,
            'language': 'en'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'session' in data
        assert data['session']['patient_id'] == sample_patient_id
        assert data['session']['language'] == 'en'
        assert data['session']['status'] == 'active'
    
    def test_create_session_missing_patient_id(self, client):
        """Test POST /api/sessions - Missing patient_id"""
        response = client.post('/api/sessions', json={
            'language': 'en'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_session_invalid_language(self, client, sample_patient_id):
        """Test POST /api/sessions - Invalid language"""
        response = client.post('/api/sessions', json={
            'patient_id': sample_patient_id,
            'language': 'xx'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_session_success(self, client, sample_session):
        """Test GET /api/sessions/{session_id} - Success"""
        response = client.get(f'/api/sessions/{sample_session.session_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session' in data
        assert data['session']['session_id'] == sample_session.session_id
    
    def test_get_session_not_found(self, client):
        """Test GET /api/sessions/{session_id} - Not found"""
        response = client.get('/api/sessions/INVALID_SESSION_ID')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_end_session_success(self, client, sample_session):
        """Test PUT /api/sessions/{session_id} - Success"""
        response = client.put(
            f'/api/sessions/{sample_session.session_id}',
            json={'status': 'completed'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['session']['status'] == 'completed'
    
    def test_end_session_invalid_status(self, client, sample_session):
        """Test PUT /api/sessions/{session_id} - Invalid status"""
        response = client.put(
            f'/api/sessions/{sample_session.session_id}',
            json={'status': 'invalid_status'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_patient_sessions(self, client, db):
        """Test GET /api/patients/{patient_id}/sessions"""
        patient_id = "P_PATIENT_TEST"
        
        # Create multiple sessions
        db.create_session(patient_id=patient_id, language="en")
        db.create_session(patient_id=patient_id, language="kn")
        
        response = client.get(f'/api/patients/{patient_id}/sessions')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['patient_id'] == patient_id
        assert len(data['sessions']) >= 2


class TestMessageManagement:
    """Test message endpoints"""
    
    def test_add_message_success(self, client, sample_session):
        """Test POST /api/sessions/{session_id}/messages - Success"""
        response = client.post(
            f'/api/sessions/{sample_session.session_id}/messages',
            json={
                'role': 'user',
                'content': 'I have a toothache',
                'turn_number': 1
            }
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'message' in data
        assert data['message']['role'] == 'user'
        assert data['message']['content'] == 'I have a toothache'
    
    def test_add_message_missing_fields(self, client, sample_session):
        """Test POST /api/sessions/{session_id}/messages - Missing fields"""
        response = client.post(
            f'/api/sessions/{sample_session.session_id}/messages',
            json={
                'role': 'user',
                # Missing 'content' and 'turn_number'
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_add_message_invalid_role(self, client, sample_session):
        """Test POST /api/sessions/{session_id}/messages - Invalid role"""
        response = client.post(
            f'/api/sessions/{sample_session.session_id}/messages',
            json={
                'role': 'invalid_role',
                'content': 'Hello',
                'turn_number': 1
            }
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_add_message_to_inactive_session(self, client, db, sample_session):
        """Test POST /api/sessions/{session_id}/messages - Inactive session"""
        # End the session
        db.end_session(sample_session.session_id)
        
        response = client.post(
            f'/api/sessions/{sample_session.session_id}/messages',
            json={
                'role': 'user',
                'content': 'Hello',
                'turn_number': 1
            }
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_messages_success(self, client, db, sample_session):
        """Test GET /api/sessions/{session_id}/messages"""
        # Add some messages
        db.add_message(
            session_id=sample_session.session_id,
            role='user',
            content='Hello',
            turn_number=1
        )
        db.add_message(
            session_id=sample_session.session_id,
            role='assistant',
            content='Hi there',
            turn_number=2
        )
        
        response = client.get(f'/api/sessions/{sample_session.session_id}/messages')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['messages']) == 2
        assert data['messages'][0]['role'] == 'user'
        assert data['messages'][1]['role'] == 'assistant'
    
    def test_get_messages_not_found(self, client):
        """Test GET /api/sessions/{session_id}/messages - Not found"""
        response = client.get('/api/sessions/INVALID_SESSION/messages')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestClinicalData:
    """Test clinical data endpoints"""
    
    def test_save_clinical_data_success(self, client, sample_session):
        """Test POST /api/sessions/{session_id}/clinical - Success"""
        clinical_info = {
            'chief_complaint': 'toothache',
            'pain_severity': 7,
            'duration': '3 days',
            'urgency_level': 'MEDIUM',
            'recommended_specialist': 'Dentist',
            'allergies': ['Penicillin']
        }
        
        response = client.post(
            f'/api/sessions/{sample_session.session_id}/clinical',
            json=clinical_info
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'clinical_data' in data
        assert data['clinical_data']['chief_complaint'] == 'toothache'
        assert data['clinical_data']['pain_severity'] == 7
    
    def test_get_clinical_data_success(self, client, db, sample_session):
        """Test GET /api/sessions/{session_id}/clinical"""
        clinical_info = {
            'chief_complaint': 'headache',
            'pain_severity': 5,
            'urgency_level': 'LOW'
        }
        db.save_clinical_data(sample_session.session_id, clinical_info)
        
        response = client.get(f'/api/sessions/{sample_session.session_id}/clinical')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['clinical_data'] is not None
        assert data['clinical_data']['chief_complaint'] == 'headache'
    
    def test_get_clinical_data_not_found(self, client):
        """Test GET /api/sessions/{session_id}/clinical - Not found"""
        response = client.get('/api/sessions/INVALID_SESSION/clinical')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestExport:
    """Test export endpoints"""
    
    def test_export_session_json_success(self, client, db, sample_session):
        """Test GET /api/sessions/{session_id}/export - Success"""
        # Add messages
        db.add_message(
            session_id=sample_session.session_id,
            role='user',
            content='Hello',
            turn_number=1
        )
        db.add_message(
            session_id=sample_session.session_id,
            role='assistant',
            content='Hi',
            turn_number=2
        )
        
        # Add clinical data
        db.save_clinical_data(
            sample_session.session_id,
            {'chief_complaint': 'pain', 'urgency_level': 'MEDIUM'}
        )
        
        response = client.get(f'/api/sessions/{sample_session.session_id}/export')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session' in data
        assert 'conversation_history' in data
        assert 'clinical_data' in data
        assert len(data['conversation_history']) == 2
    
    def test_export_session_json_not_found(self, client):
        """Test GET /api/sessions/{session_id}/export - Not found"""
        response = client.get('/api/sessions/INVALID_SESSION/export')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_not_found(self, client):
        """Test 404 for invalid endpoint"""
        response = client.get('/api/invalid/endpoint')
        assert response.status_code == 404
    
    def test_malformed_json(self, client):
        """Test malformed JSON request"""
        response = client.post(
            '/api/sessions',
            data='{"invalid json}',
            content_type='application/json'
        )
        # Flask returns 400 for malformed JSON
        assert response.status_code in [400, 415]
    
    def test_missing_content_type(self, client, sample_patient_id):
        """Test request without Content-Type header"""
        response = client.post(
            '/api/sessions',
            data='{"patient_id": "' + sample_patient_id + '"}',
            content_type=None
        )
        # Should still work or return appropriate error
        assert response.status_code in [201, 400, 415]


class TestDatabaseOperations:
    """Test database layer operations"""
    
    def test_create_session_db(self, db):
        """Test database session creation"""
        session = db.create_session(patient_id="P_DB_TEST", language="kn")
        
        assert session.session_id is not None
        assert session.patient_id == "P_DB_TEST"
        assert session.language == "kn"
        assert session.status == "active"
    
    def test_get_session_db(self, db):
        """Test database session retrieval"""
        created_session = db.create_session(patient_id="P_DB_TEST_2", language="en")
        retrieved_session = db.get_session_by_id(created_session.session_id)
        
        assert retrieved_session is not None
        assert retrieved_session.session_id == created_session.session_id
        assert retrieved_session.patient_id == "P_DB_TEST_2"
    
    def test_end_session_db(self, db):
        """Test database session ending"""
        session = db.create_session(patient_id="P_DB_TEST_3")
        ended_session = db.end_session(session.session_id)
        
        assert ended_session.status == "completed"
        assert ended_session.ended_at is not None
    
    def test_add_message_db(self, db):
        """Test database message creation"""
        session = db.create_session(patient_id="P_DB_TEST_4")
        message = db.add_message(
            session_id=session.session_id,
            role='user',
            content='Test message',
            turn_number=1,
            confidence=0.95
        )
        
        assert message.content == 'Test message'
        assert message.confidence == 0.95
    
    def test_get_messages_db(self, db):
        """Test database message retrieval"""
        session = db.create_session(patient_id="P_DB_TEST_5")
        
        db.add_message(session.session_id, 'user', 'Message 1', 1)
        db.add_message(session.session_id, 'assistant', 'Message 2', 2)
        
        messages = db.get_messages(session.session_id)
        
        assert len(messages) == 2
        assert messages[0].role == 'user'
        assert messages[1].role == 'assistant'
    
    def test_save_clinical_data_db(self, db):
        """Test database clinical data saving"""
        session = db.create_session(patient_id="P_DB_TEST_6")
        
        clinical_data = db.save_clinical_data(
            session.session_id,
            {
                'chief_complaint': 'fever',
                'pain_severity': 6,
                'urgency_level': 'HIGH',
                'allergies': ['Aspirin']
            }
        )
        
        assert clinical_data.chief_complaint == 'fever'
        assert clinical_data.urgency_level == 'HIGH'
        assert clinical_data.allergies == ['Aspirin']
    
    def test_export_session_json_db(self, db):
        """Test database JSON export"""
        session = db.create_session(patient_id="P_DB_TEST_7")
        
        db.add_message(session.session_id, 'user', 'Hello', 1)
        db.add_message(session.session_id, 'assistant', 'Hi', 2)
        
        db.save_clinical_data(
            session.session_id,
            {'chief_complaint': 'cough', 'urgency_level': 'LOW'}
        )
        
        export = db.export_session_as_json(session.session_id)
        
        assert export is not None
        assert 'session' in export
        assert 'conversation_history' in export
        assert len(export['conversation_history']) == 2
    
    def test_health_check_db(self, db):
        """Test database health check"""
        is_healthy = db.health_check()
        assert is_healthy is True


class TestIntegration:
    """Integration tests combining multiple endpoints"""
    
    def test_full_conversation_flow(self, client, db):
        """Test complete conversation workflow"""
        patient_id = "P_INTEGRATION_TEST"
        
        # 1. Create session
        response = client.post('/api/sessions', json={
            'patient_id': patient_id,
            'language': 'en'
        })
        assert response.status_code == 201
        session_id = json.loads(response.data)['session']['session_id']
        
        # 2. Add messages
        response = client.post(
            f'/api/sessions/{session_id}/messages',
            json={
                'role': 'user',
                'content': 'I have symptoms',
                'turn_number': 1
            }
        )
        assert response.status_code == 201
        
        # 3. Save clinical data
        response = client.post(
            f'/api/sessions/{session_id}/clinical',
            json={
                'chief_complaint': 'symptoms',
                'urgency_level': 'MEDIUM'
            }
        )
        assert response.status_code == 201
        
        # 4. Export JSON
        response = client.get(f'/api/sessions/{session_id}/export')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['session']['session_id'] == session_id
        
        # 5. End session
        response = client.put(
            f'/api/sessions/{session_id}',
            json={'status': 'completed'}
        )
        assert response.status_code == 200
        assert json.loads(response.data)['session']['status'] == 'completed'
