from rest_framework.renderers import JSONRenderer

class EnvelopeJSONRenderer(JSONRenderer):
    """
    Wraps all API responses in a consistent format:
    { "status": "success" | "error", "data": {}, "message": "" }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context['response'].status_code
        response_dict = {
            'status': 'success' if status_code < 400 else 'error',
            'data': data,
            'message': ''
        }

        # Handle DRF Pagination extraction
        if isinstance(data, dict) and 'results' in data:
            response_dict['data'] = data['results']
            response_dict['pagination'] = {
                'count': data.get('count'),
                'next': data.get('next'),
                'previous': data.get('previous')
            }

        # Extract error messages gracefully
        if status_code >= 400 and isinstance(data, dict) and 'detail' in data:
            response_dict['message'] = data.pop('detail')
            response_dict['data'] = data # Remaining validation errors

        return super().render(response_dict, accepted_media_type, renderer_context)