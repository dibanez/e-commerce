"""
Context processors for core app.
"""


def search(request):
    """
    Add search query to template context.
    """
    return {
        'search_query': request.GET.get('q', ''),
    }