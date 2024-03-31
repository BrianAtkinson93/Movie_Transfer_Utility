.PHONY: clean build

all: build

clean:
	@echo "Cleaning up build directories..."
	rm -rf build/ dist/

build: clean
	@echo "Building with PyInstaller..."
	@. .venv/bin/activate && pyinstaller --clean move_to_plex.spec
