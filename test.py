def greet(name: str) -> str:
    """Return a friendly greeting for the given name.

    Args:
        name: The name of the person to greet.

    Returns:
        A greeting string in the format "Hello, {name}!".
    """
    return f"Hello, {name}!"


def main() -> None:
    """Simple demonstration of the ``greet`` function.

    Runs a few example greetings when the module is executed directly.
    """
    examples = ["World", "ForgeAI", "User"]
    for example in examples:
        print(greet(example))


if __name__ == "__main__":
    main()
