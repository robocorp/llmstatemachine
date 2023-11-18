import argparse
import math
import re
from typing import Iterable, List, Optional, Set, cast

from bs4 import BeautifulSoup, Comment, NavigableString, PageElement, Tag


def remove_html_comments_and_doctype(html_string: str) -> str:
    """
    Removes HTML comments and the doctype declaration from a string containing HTML.
    """
    comment_pattern = (
        r"<!--(.*?)-->"  # Regular expression pattern to match HTML comments
    )
    doctype_pattern = r"<!DOCTYPE.*?>"  # Regular expression pattern to match doctype

    # Remove comments
    html_string = re.sub(comment_pattern, "", html_string, flags=re.DOTALL)

    # Remove doctype
    html_string = re.sub(doctype_pattern, "", html_string, flags=re.IGNORECASE)

    return html_string


def collapse_html_elements(html: str, collapsed_elements: List[str]) -> BeautifulSoup:
    html = remove_html_comments_and_doctype(html)
    soup = BeautifulSoup(html, "html.parser")

    for name in collapsed_elements:
        for elem in soup.select(name):
            comment_parts = []

            # Collapse attributes and comment about it
            attr_count = len(elem.attrs)
            if attr_count:
                comment_parts.append(f"{attr_count} attrs")
                elem.attrs = {}  # Clearing all attributes at once

            # Check for direct textual content
            if elem.string:
                char_count = len(elem.string)
                line_count = len(elem.string.splitlines())
                comment_parts.append(f"{char_count} chars, {line_count} lines")

            # Check for child elements
            child_count = len(list(elem.children))
            if child_count:
                comment_parts.append(f"{child_count} elems")

            comment_text = f"Content collapsed: {', '.join(comment_parts)} omitted"
            comment = Comment(comment_text)

            elem.clear()
            elem.append(comment)  # append the comment to the cleared element

    return soup


def pluralize(count: int) -> str:
    """Return 'item' or 'items' based on the count."""
    return "item" if count == 1 else "items"


def shortened_string(
    content: str,
    focus_text: str,
    max_string_length: int = 50,
    context_length: int = 5,
) -> str:
    # If content fits within max_string_length, return as is
    if len(content) <= max_string_length:
        return content

    # If focus is present and fits within the length constraint
    if focus_text and focus_text in content:
        start_idx = max(content.find(focus_text) - context_length, 0)
        end_idx = min(
            content.find(focus_text) + len(focus_text) + context_length,
            len(content),
        )

        # Adjust indices to ensure the output length fits max_string_length
        length_diff = max_string_length - (end_idx - start_idx)
        half_diff = length_diff // 2
        start_idx = max(start_idx - half_diff, 0)
        end_idx = min(end_idx + half_diff, len(content))

        truncated_str = content[start_idx:end_idx]
        ellipsis_prefix = ".." if start_idx > 0 else ""
        ellipsis_suffix = ".." if end_idx < len(content) else ""

        return f"{ellipsis_prefix}{truncated_str}{ellipsis_suffix}"

    # No focus, just general shortening
    breakpoints = [" ", "/", ".", ",", ";", "-", "_"]  # typical breakpoints
    # No focus, just general shortening
    mid_idx = len(content) // 2
    left_break = mid_idx
    right_break = mid_idx

    # Search left from the midpoint for a natural breakpoint
    while left_break > 0 and content[left_break] not in breakpoints:
        left_break -= 1

    # Search right from the midpoint for a natural breakpoint
    while right_break < len(content) and content[right_break] not in breakpoints:
        right_break += 1

    begin_part = content[:left_break]
    end_part = content[right_break:]

    # If the total length exceeds max_string_length, adjust the lengths
    while len(begin_part) + len(end_part) + 2 > max_string_length:  # plus 2 for ".."
        # If one part is longer, trim it first. Otherwise, trim both.
        if len(begin_part) > len(end_part):
            begin_part = begin_part[:-1]
        elif len(end_part) > len(begin_part):
            end_part = end_part[1:]
        else:
            begin_part = begin_part[:-1]
            end_part = end_part[1:]

    return f"{begin_part}..{end_part}"


def attributes_with_focus_text(tag: Tag, focus_text: str) -> List[str]:
    """Return attributes that contain the focus target text."""
    if not focus_text:
        return []
    return [attr for attr, value in tag.attrs.items() if focus_text in str(value)]


def children_with_focus_text(
    children: Iterable[PageElement], focus_text: str
) -> List[int]:
    """Return child element indecies that contain the focus target text."""
    if not focus_text:
        return []
    return [index for index, child in enumerate(children) if focus_text in str(child)]


def format_content(
    content: NavigableString, focus_text: str, max_content_size: int
) -> str:
    if isinstance(content, Comment):
        return f"<!-- {content} --->"
    return shortened_string(
        str(content).strip(), focus_text, max_string_length=max(max_content_size, 50)
    )


def format_attributes(
    tag: Tag,
    attribute_priority: List[str],
    focus_text: str,
    max_size_for_attrs: int,
) -> List[str]:
    # Initialize
    attrs_to_show: List[str] = []
    current_size = 0
    hidden_attr_count = 0

    # Function to try adding an attribute and update current_size
    def try_add_attribute(attr: str, val: str) -> bool:
        nonlocal current_size
        if isinstance(val, list):
            val = " ".join(val)
        val = shortened_string(val, focus_text)
        attr_str = f' {attr}="{val}"'
        new_size = current_size + len(attr_str)
        if new_size <= max_size_for_attrs:
            attrs_to_show.append(attr_str)
            current_size = new_size
            return True
        return False

    all_attrs: Set[str] = set(tag.attrs.keys())

    # Add focused attributes
    focused_attrs = attributes_with_focus_text(tag, focus_text)
    for attr in focused_attrs:
        if attr in all_attrs:
            if not try_add_attribute(attr, cast(str, tag[attr])):
                hidden_attr_count += 1
            all_attrs.remove(attr)

    # Add priority attributes
    for attr in attribute_priority:
        if attr in all_attrs:
            if not try_add_attribute(attr, cast(str, tag[attr])):
                hidden_attr_count += 1
            all_attrs.remove(attr)

    # Add other attributes
    for attr in sorted(all_attrs):
        if not try_add_attribute(attr, cast(str, tag[attr])):
            hidden_attr_count += 1

    # Add hidden attribute count if necessary
    if hidden_attr_count > 0:
        attrs_to_show.append(f" .. (+{hidden_attr_count} attrs)")

    return attrs_to_show


def format_children(
    children: List[PageElement],
    separator: str,
    focus_text: str,
    attribute_priority: List[str],
    max_size_for_children: int,
    max_child_elements: int = 5,
) -> List[str]:
    """Handle the children of a tag."""

    # Get focused children
    focused_children = children_with_focus_text(children, focus_text)[
        :max_child_elements
    ]

    # Determine the total slots available for non-focused children
    slots_for_others = max_child_elements - len(focused_children)

    # Collect the children to be displayed, giving priority to focused children
    children_to_display = sorted(
        set(
            focused_children
            + [
                index
                for index, child in enumerate(children)
                if child not in focused_children
            ][:slots_for_others]
        )
    )

    running_index = 0  # This tracks where we are in the original list of all children
    all_children_list = list(children)

    size_of_displayed_children = sum(
        len(str(all_children_list[child_index])) for child_index in children_to_display
    )

    result: List[str] = []
    for child_index in children_to_display:
        # Get the original index of the child
        child = all_children_list[child_index]

        child_total_size = len(str(child))
        allocated_size = int(
            max_size_for_children * child_total_size / size_of_displayed_children
        )

        # Calculate the number of skipped children between the running index and the current index
        skipped = child_index - running_index

        # Add a placeholder for skipped children, if any
        if skipped:
            skipped_word = "items" if skipped > 1 else "item"
            result.append(f"<!-- .. skipped {skipped} {skipped_word} .. -->")

        # Append the child to the result
        result.append(
            format_element(
                child,
                separator,
                focus_text,
                attribute_priority,
                allocated_size,
            )
        )

        # Update the running index
        running_index = child_index + 1

    # Add a placeholder for any remaining hidden children
    hidden_count = len(all_children_list) - running_index
    if hidden_count > 0:
        hidden_word = "items" if hidden_count > 1 else "item"
        result.append(f"<!-- .. skipped {hidden_count} {hidden_word} .. -->")

    return result


def format_element(
    tag: PageElement,
    separator: str,
    focus_text: str,
    attribute_priority: List[str],
    max_element_size: int,
) -> str:
    if isinstance(tag, NavigableString):
        return format_content(tag, focus_text, max_element_size)

    if not isinstance(tag, Tag):
        return separator + f"unknown {tag}"

    pretty_tag = str(tag)
    if max_element_size >= len(pretty_tag):
        return separator + pretty_tag

    # Calculate size of attributes in pretty format
    attrs_size = sum(len(f' {attr}="{value}"') for attr, value in tag.attrs.items())

    # Calculate size of children in str format
    children_size = sum(
        len(str(child))
        for child in tag.children
        if isinstance(child, (Tag, NavigableString))
    )

    attrs_and_children_size = attrs_size + children_size

    if attrs_and_children_size == 0:
        return f"{separator}<{tag.name}/>"

    if children_size == 0:
        attrs = "".join(
            format_attributes(
                tag,
                attribute_priority,
                focus_text,
                max_element_size - len(f"{separator}<{tag.name}/>"),
            )
        )
        return f"{separator}<{tag.name}{attrs}/>"

    tag_part_without_attrs_and_children = len(f"{separator}<{tag.name}></{tag.name}>")

    max_size_for_children = max(
        int(
            (max_element_size - tag_part_without_attrs_and_children)
            * children_size
            / attrs_and_children_size
        ),
        0,
    )

    children = "".join(
        format_children(
            list(tag.children),
            separator,
            focus_text,
            attribute_priority,
            max_size_for_children,
        )
    )

    max_size_for_attrs = (
        max_element_size - tag_part_without_attrs_and_children - len(children)
    )

    attrs = "".join(
        format_attributes(tag, attribute_priority, focus_text, max_size_for_attrs)
    )
    return f"{separator}<{tag.name}{attrs}>{children}</{tag.name}>"


def truncate_until(original_html: str, focus_text: str, max_total_length: int) -> str:
    # Direct return if no focus_text is defined or if no truncation is needed
    if len(original_html) <= max_total_length:
        return original_html

    # Find all occurrences of focus_text
    matches = focus_text and list(re.finditer(focus_text, original_html))
    if not matches or not focus_text:
        # If no matches, return the truncated string with an omission message
        return (
            original_html[:max_total_length]
            + f" .. {len(original_html) - max_total_length} characters omitted"
        )

    # Calculate the segments to preserve
    preserved_segments = [(m.start(), m.end()) for m in matches]

    # Sort and merge overlapping segments
    preserved_segments.sort()
    merged_segments = []
    for start, end in preserved_segments:
        if merged_segments and start <= merged_segments[-1][1]:
            merged_segments[-1] = (
                merged_segments[-1][0],
                max(merged_segments[-1][1], end),
            )
        else:
            merged_segments.append((start, end))

    # Calculate the total length of preserved segments
    preserved_length = sum(end - start for start, end in merged_segments)
    remaining_length = max_total_length - preserved_length

    # Ensure preserved_length does not exceed max_total_length
    if remaining_length < 0:
        return (
            "".join(original_html[start:end] for start, end in merged_segments)[
                :max_total_length
            ]
            + " ..."
        )

    # Identify the segments of content to be truncated
    truncated_segments = []
    last_end = 0
    for start, end in merged_segments:
        truncated_segments.append(original_html[last_end:start])
        last_end = end
    truncated_segments.append(
        original_html[last_end:]
    )  # Add the final segment after the last focus_text

    # Build the truncated HTML with preserved segments and distribute remaining space
    truncated_html = ""
    for i in range(len(truncated_segments)):
        # Calculate the length to be allocated to this segment
        segment_length = remaining_length // max(1, (len(truncated_segments) - i))

        # If the calculated segment length is 0 and there is remaining length, allocate 1 character
        segment_length = max(1, segment_length) if remaining_length > 0 else 0

        truncated_html += truncated_segments[i][:segment_length]
        remaining_length -= len(truncated_segments[i][:segment_length])
        if remaining_length <= 0:
            break

    # Concatenate preserved segments with truncated segments
    last_end = 0
    for start, end in merged_segments:
        truncated_html += original_html[last_end:start]
        truncated_html += original_html[start:end]
        last_end = end
    truncated_html += original_html[last_end : max_total_length - len(truncated_html)]

    # Indicate if characters are omitted
    omitted_len = len(original_html) - len(truncated_html)
    if omitted_len > 0:
        truncated_html += f" .. {omitted_len} characters omitted"

    return truncated_html


def pretty_print_html(
    html_content: str,
    attribute_priority: Optional[List[str]] = None,
    collapsed_elements: Optional[List[str]] = None,
    focus_text: str = "",
    max_total_length: int = 4000,
) -> str:
    separator = "\n"
    if len(html_content) <= max_total_length:
        return html_content

    soup = collapse_html_elements(html_content, collapsed_elements or [])

    html_after_collapsed_elements = soup.prettify()
    if len(html_after_collapsed_elements) <= max_total_length:
        return html_after_collapsed_elements

    formatted_html = separator.join(
        format_children(
            soup.contents,
            separator,
            focus_text,
            attribute_priority or [],
            max_total_length,
        )
    )
    return truncate_until(formatted_html, focus_text, max_total_length)


def html_explorer(
    html_content: str,
    attribute_priority: Optional[List[str]] = None,
    collapsed_elements: Optional[List[str]] = None,
    focus_text: str = "",
    css_selector: str = "",
    max_total_length=4000,
    max_matches=20,
) -> str:
    post_fix = ""
    # Filter by CSS selector if provided
    if css_selector:
        soup = BeautifulSoup(html_content, "html.parser")
        filtered_elements = soup.select(css_selector)
        html_content = "\n".join(str(elem) for elem in filtered_elements[:max_matches])
        if len(filtered_elements) > max_matches:
            post_fix = f"\n .. {len(filtered_elements) - max_matches} additional matching elements"

    return (
        pretty_print_html(
            html_content,
            focus_text=focus_text,
            attribute_priority=attribute_priority,
            collapsed_elements=collapsed_elements,
            max_total_length=max_total_length,
        )
        + post_fix
    )


if __name__ == "__main__":
    # Initialize argparse with ArgumentDefaultsHelpFormatter
    argparser = argparse.ArgumentParser(
        description="Pretty Print HTML from file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Add required and optional arguments
    argparser.add_argument(
        "file_path", help="Path to the HTML file to be read.", type=str
    )
    argparser.add_argument(
        "--focus",
        help="Specify text to focus on in the HTML extraction. The output will include the text and its surrounding structural elements. Leave empty to disable this feature.",
        default="",
        type=str,
    )
    argparser.add_argument(
        "--priority_attributes",
        help="Attributes to be prioritized to show, separated by commas.",
        default="class",
        type=str,
    )
    argparser.add_argument(
        "--collapsed_elements",
        help="Elements to be collapsed, separated by commas.",
        default="script,style,svg,head,source,track",
        type=str,
    )
    argparser.add_argument(
        "--css_selector",
        help="CSS selector to filter elements. Leave empty to disable filtering.",
        default="",
        type=str,
    )

    # Parse arguments
    args = argparser.parse_args()

    # Extract individual arguments
    file_path = args.file_path
    collapsed_elements = args.collapsed_elements.split(",")

    # Read the HTML file
    with open(file_path) as f:
        html_content = f.read()

    # Pretty print HTML
    print(
        html_explorer(
            html_content,
            focus_text=args.focus,
            attribute_priority=args.priority_attributes.split(","),
            collapsed_elements=collapsed_elements,
            css_selector=args.css_selector,
            max_total_length=4000 * 4,
        )
    )
