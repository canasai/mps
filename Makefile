all:

test:
	python -m mps.tests.test_mps mps/default_config.json

clean:
	rm -f *.log *.out
