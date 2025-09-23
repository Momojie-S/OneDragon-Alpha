# -*- coding: utf-8 -*-
import asyncio
import sys

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse


async def execute_python_code_by_path(
    code_file_path: str,
    timeout: float = 300,
) -> ToolResponse:
    """Execute the given python code in a temp file and capture the return
    code, standard output and error. Note you must `print` the output to get
    the result, and the tmp file will be removed right after the execution.

    Args:
        code_file_path (`str`):
            .py file path to execute
        timeout (`float`, defaults to `300`):
            The maximum time (in seconds) allowed for the code to run.

    Returns:
        `ToolResponse`:
            The response containing the return code, standard output, and
            standard error of the executed code.
    """
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-u",
        code_file_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout)
        stdout, stderr = await proc.communicate()
        stdout_str = stdout.decode("utf-8")
        stderr_str = stderr.decode("utf-8")
        returncode = proc.returncode

    except asyncio.TimeoutError:
        stderr_suffix = (
            f"TimeoutError: The code execution exceeded "
            f"the timeout of {timeout} seconds."
        )
        returncode = -1
        try:
            proc.terminate()
            stdout, stderr = await proc.communicate()
            stdout_str = stdout.decode("utf-8")
            stderr_str = stderr.decode("utf-8")
            if stderr_str:
                stderr_str += f"\n{stderr_suffix}"
            else:
                stderr_str = stderr_suffix
        except ProcessLookupError:
            stdout_str = ""
            stderr_str = stderr_suffix

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=f"<returncode>{returncode}</returncode>"
                f"<stdout>{stdout_str}</stdout>"
                f"<stderr>{stderr_str}</stderr>",
            ),
        ],
    )
