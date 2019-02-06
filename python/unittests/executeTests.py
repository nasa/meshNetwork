import sys, pytest
sys.path.append('../')

# Execute requested test
if len(sys.argv) > 1:
    pytest.main([sys.argv[1]])
else:
    pytest.main()
