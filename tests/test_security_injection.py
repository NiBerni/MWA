def test_t_string_prevents_sql_injection(client, clean_database):
	"""
	Demonstrate that t-strings (via tstring) treat input as literal values,
	not executable SQL.
	"""
	# A malicious payload that would terminate a standard string query
	malicious_id = "1 OR 1=1"
	
	# We expect our backend using tstring() to handle this safely as a literal,
	# resulting in a 404 (not found) rather than a successful injection of all records.
	response = client.delete(f"/api/favorites/{malicious_id}")
	
	# The system should treat this as a string literal search, fail to find the ID,
	# and return 404, not 204 (Success)
	assert response.status_code == 404
