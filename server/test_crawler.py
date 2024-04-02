import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from crawler import get_links, get_page_priority, bidirectional_search, find_path_async, PathNotFoundError, PathFindingErrorWithLogs

@pytest.mark.asyncio
async def test_get_links():
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.text.return_value = '''
            <html>
                <body>
                    <a href="/wiki/Page1">Page 1</a>
                    <a href="/wiki/Page2">Page 2</a>
                    <a href="https://example.com">External Link</a>
                </body>
            </html>
        '''
        mock_session.return_value.__aenter__.return_value.get.return_value = mock_response

        with patch('redis.Redis', return_value=MagicMock()) as mock_redis:
            mock_redis.return_value.get.return_value = None
            links = await get_links(mock_session, 'https://en.wikipedia.org/wiki/Main_Page')
            assert len(links) == 2
            assert 'https://en.wikipedia.org/wiki/Page1' in links
            assert 'https://en.wikipedia.org/wiki/Page2' in links

@pytest.mark.asyncio
async def test_get_page_priority():
    page1 = 'https://en.wikipedia.org/wiki/Italian_Renaissance'
    page2 = 'https://en.wikipedia.org/wiki/Potato'
    finish_page = 'https://en.wikipedia.org/wiki/Leonardo_da_Vinci'

    priority1 = get_page_priority(page1, finish_page)
    priority2 = get_page_priority(page2, finish_page)

    assert priority1 < priority2

    exact_match_page = 'https://en.wikipedia.org/wiki/Leonardo_da_Vinci'
    exact_match_priority = get_page_priority(exact_match_page, finish_page)

    assert exact_match_priority == float('-inf')

@pytest.mark.asyncio
async def test_bidirectional_search():
    start_page = 'https://en.wikipedia.org/wiki/Leonardo_da_Vinci'
    finish_page = 'https://en.wikipedia.org/wiki/French_fries'

    with patch('aiohttp.ClientSession') as mock_session:
        mock_get_links = AsyncMock(side_effect=[
            ['https://en.wikipedia.org/wiki/Italian_Renaissance', 'https://en.wikipedia.org/wiki/Polymath'],
            ['https://en.wikipedia.org/wiki/Potato', 'https://en.wikipedia.org/wiki/Belgium'],
            ['https://en.wikipedia.org/wiki/French_fries'],
            ['https://en.wikipedia.org/wiki/France'],
            ['https://en.wikipedia.org/wiki/French_fries']
        ])
        mock_session.return_value.__aenter__.return_value.get.return_value.text.return_value = ''

        with patch('crawler.get_links', mock_get_links):
            path = await bidirectional_search(start_page, finish_page)
            assert path == [start_page, 'https://en.wikipedia.org/wiki/Italian_Renaissance', 'https://en.wikipedia.org/wiki/Potato', 'https://en.wikipedia.org/wiki/Belgium', finish_page]

@pytest.mark.asyncio
async def test_find_path_async():
    start_page = 'https://en.wikipedia.org/wiki/Leonardo_da_Vinci'
    finish_page = 'https://en.wikipedia.org/wiki/French_fries'

    with patch('crawler.bidirectional_search') as mock_bidirectional_search:
        mock_bidirectional_search.return_value = [start_page, 'https://en.wikipedia.org/wiki/Italian_Renaissance', 'https://en.wikipedia.org/wiki/Potato', finish_page]

        path, logs, time_taken, discovered = await find_path_async(start_page, finish_page)
        assert path == [start_page, 'https://en.wikipedia.org/wiki/Italian_Renaissance', 'https://en.wikipedia.org/wiki/Potato', finish_page]
        assert isinstance(logs, list)
        assert isinstance(time_taken, float)
        assert isinstance(discovered, int)

    with patch('crawler.bidirectional_search', return_value=None):
        with pytest.raises(PathNotFoundError):
            await find_path_async(start_page, finish_page)

    with patch('crawler.bidirectional_search', side_effect=Exception('Test Exception')):
        with pytest.raises(PathFindingErrorWithLogs):
            await find_path_async(start_page, finish_page)