import argparse

from dotenv import load_dotenv

from html_extractor import html_explorer
from workflow_agent import WorkflowAgentBuilder

load_dotenv()


# [INIT] => [FOCUS or SELECT]
# [SELECTED_NON_EMPTY] => [FOCUS or SELECT or VALIDATE]
# [VALIDATE] => [FOCUS or SELECT or VALIDATE or RESULT]
# <DONE>


def focus(argument: str):
    """when searching for texts in the html,

    Parameters
    ----------
    argument : str
        The focused text to find from html.
    """
    output = html_explorer(html_content, focus_text=argument, max_total_length=3000)
    return f"""focus "{argument}":\n```\n{output}\n```""", "INIT"


def select(argument: str):
    """when selecting all elements matching the css selector.

    Parameters
    ----------
    argument : str
        The css selector candidate..
    """
    value = html_explorer(html_content, css_selector=argument, max_matches=20)
    if not result:
        return (
            f"""select "{argument}" did not return any elements.""",
            "INIT",
        )
    return (
        f"""select "{argument}":\n```\n{value}\n```""",
        "SELECTED_NON_EMPTY",
    )


def validate(argument: str):
    """when you think the correct css selector is known.

    Parameters
    ----------
    argument : str
        The css selector used.
    """
    output = html_explorer(html_content, css_selector=argument, max_matches=10000)
    if not output:
        return (
            f"""validate "{argument}" did not return any elements.""",
            "SELECTED_NON_EMPTY",
        )
    for expectation in expectations:
        if expectation in argument:
            return (
                f"""validate "{argument}" failed: css selector contains text "{expectation}". """
                + "Do not use the expected text in the selector.",
                "SELECTED_NON_EMPTY",
            )
        if expectation not in output:
            return (
                f"""validate "{argument}" did not contain element with "{expectation}".""",
                "SELECTED_NON_EMPTY",
            )
    return (
        f"""validate "{argument}" seems valid.""",
        "VALIDATED",
    )


def result(argument: str):
    """when the correct css selector is known.

    Parameters
    ----------
    argument : str
       The response to user with the css selector included.
    """
    return argument, "DONE"


if __name__ == "__main__":
    # Initialize argparse with ArgumentDefaultsHelpFormatter
    argparser = argparse.ArgumentParser(
        description="HTML Element Selector finding agent",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Add required and optional arguments
    argparser.add_argument(
        "file_path", help="Path to the HTML file to be read.", type=str
    )

    # Parse arguments
    args = argparser.parse_args()

    # Extract individual arguments
    file_path = args.file_path

    # Read the HTML file
    with open(file_path) as f:
        html_content = f.read()

    print("--- Give few examples that should be discovered with correct selector ---")
    examples: list[str] = []
    while True:
        example = input("Example text: ").strip()
        if not example:
            break
        if example not in html_content:
            print("Can't find the example text from the html! - skipping")
            continue
        examples.append(example)

    examples_str = '"' + '", "'.join(examples) + '"'
    expectations = examples
    builder = WorkflowAgentBuilder()
    builder.add_state_and_transitions("INIT", {focus, select})
    builder.add_state_and_transitions("SELECTED_NON_EMPTY", {focus, select, validate})
    builder.add_state_and_transitions("VALIDATED", {focus, select, validate, result})
    builder.add_end_state("DONE")
    workflow_agent = builder.build()
    workflow_agent.add_message(
        {
            "role": "system",
            "content": "You are a helpful HTML css selector finding assistant.",
        }
    )
    workflow_agent.add_message(
        {
            "role": "user",
            "content": (
                "Assignment: Create CSS Selectors Based on Text Content\n"
                "Your task is to develop CSS selectors that can target HTML elements containing specific text contents. "
                "You are provided with a list of example texts. Use these examples to create selectors that can identify "
                "elements containing these texts in a given HTML structure.\n\n"
                "Instructions:\n"
                f"- Use the provided list of examples: {examples_str}.\n"
                "Your goal is to create selectors that are both precise and efficient, tailored to the specific"
                " content and structure of the HTML elements."
            ),
        }
    )
    for message in workflow_agent.messages:
        print(str(message)[:160])
    print(">" * 80)
    res = "NO RESULT"
    while workflow_agent.current_state != "DONE":
        res = workflow_agent.step()
    print(res)
