import argparse

from dotenv import load_dotenv

from html_extractor import html_explorer
from llmstatemachine import WorkflowAgentBuilder, set_next_state

load_dotenv()


# [INIT] => [FOCUS or SELECT]
# [SELECTED_NON_EMPTY] => [FOCUS or SELECT or VALIDATE]
# [VALIDATE] => [FOCUS or SELECT or VALIDATE or RESULT]
# <DONE>


def focus(argument: str):
    output = html_explorer(html_content, focus_text=argument, max_total_length=3000)
    return f"""focus "{argument}":\n```\n{output}\n```"""


def select(argument: str):
    value = html_explorer(html_content, css_selector=argument, max_matches=20)
    if not result:
        set_next_state("INIT")
        return f"select '{argument}' did not return any elements."
    set_next_state("SELECTED_NON_EMPTY")
    return f"""select "{argument}":\n```\n{value}\n```"""


def validate(argument: str):
    output = html_explorer(html_content, css_selector=argument, max_matches=10000)
    if not output:
        set_next_state("SELECTED_NON_EMPTY")
        return f"validate '{argument}' did not return any elements."
    for expectation in expectations:
        if expectation in argument:
            set_next_state("SELECTED_NON_EMPTY")
            return (
                f"""validate "{argument}" failed: css selector contains text "{expectation}". """
                + "Do not use the expected text in the selector."
            )
        if expectation not in output:
            set_next_state("SELECTED_NON_EMPTY")
            return (
                f"""validate "{argument}" did not contain element with "{expectation}".""",
            )
    set_next_state("VALIDATED")
    return (f"""validate "{argument}" seems valid.""",)


def result(argument: str):
    set_next_state("DONE")
    return argument


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
    builder.add_system_message(
        (
            "You are a helpful HTML css selector finding assistant.\n"
            "Assignment: Create CSS Selectors Based on Text Content.\n"
            "Your task is to develop CSS selectors that can target HTML elements containing specific text contents. "
            "You are provided with a list of example texts. Use these examples to create selectors that can identify "
            "elements containing these texts in a given HTML structure.\n\n"
            "Instructions:\n"
            f"- Use the provided list of examples: {examples_str}.\n"
            "Your goal is to create selectors that are both precise and efficient, tailored to the specific"
            " content and structure of the HTML elements."
        )
    )
    builder.add_state_and_transitions("INIT", {focus, select})
    builder.add_state_and_transitions("SELECTED_NON_EMPTY", {focus, select, validate})
    builder.add_state_and_transitions("VALIDATED", {focus, select, validate, result})
    builder.add_end_state("DONE")
    workflow_agent = builder.build()
    print(workflow_agent.run())
