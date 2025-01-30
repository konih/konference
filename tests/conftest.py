import pytest
import asyncio

# Set asyncio as the default event loop for all async tests
pytest.register_assert_rewrite("pytest_asyncio")


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest-asyncio defaults."""
    config.option.asyncio_mode = "strict"
    # Set default loop scope to function
    config.option.asyncio_loop_scope = "function"


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Create and set a new event loop policy for all tests."""
    return asyncio.get_event_loop_policy()


# Mark only async tests to use function-scoped event loops
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Add asyncio marks to async tests."""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio(loop_scope="function"))
