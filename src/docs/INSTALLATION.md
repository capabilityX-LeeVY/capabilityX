## UV installation

Universal Visualizer (UV) is a powerful tool that simplifies the process of running and managing test cases. It provides a user-friendly interface for executing Python scripts, managing dependencies, and visualizing results.

step 1, install the UV tool:

```bash
pip install uv
```

step 2, init the project in the first time:

```bash
uv init

uv add -r requirements.txt
```

step 3, install the dependencies:

```bash
uv sync
```

step 4, add the dependencies to the project:

```bash
uv add paramiko==3.5.1
```

step 5, remove the dependencies from the project:

```bash
uv remove paramiko
```