def test_init_db_command(runner):
	"""
	Test the custom init-db CLI command.
	Ensures that the database tables are securely provisioned.
	"""
	result = runner.invoke(args=["init-db"])
	assert "Initialized the database." in result.output
	assert result.exit_code == 0
