import { json } from '@sveltejs/kit';
import {
    BACKEND_URL
} from '$env/static/private';

const BACKEND_TIMEOUT = 14000; // slightly less than client timeout

export async function POST({ request }){
        try {
            const payload = await request.json()
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), BACKEND_TIMEOUT);

            const response = await fetch(`${BACKEND_URL}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            clearTimeout(timeoutId)
        
        if (!response.ok) {
            const error = await response.json();
            return json(
                { message: error.message || 'Backend request failed' },
                { status: response.status }
            );
        }
        return response
    } catch (error) {
        clearTimeout(timeoutId);
        console.error('Error fetching chat completion: ', error);
        return new Response('Server Problem!')
    }
};
