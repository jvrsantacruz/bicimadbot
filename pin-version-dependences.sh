# Input: requirements.txt file with unversioned dependences
# Output: list of versioned dependences as in current venv
# Ej: $ ./pin-version-dependences requirements.txt > requirements-fixed.txt
pip freeze | grep -iF -f $1
