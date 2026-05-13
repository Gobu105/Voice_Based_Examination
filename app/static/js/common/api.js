export async function apiGet(url) {

    const response =
        await fetch(url, {
            credentials: "same-origin"
        });

    return handleResponse(response);
}


export async function apiPost(
    url,
    data = {}
) {

    const response =
        await fetch(url, {

            method: "POST",

            credentials:
                "same-origin",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body:
                JSON.stringify(data)
        });

    return handleResponse(response);
}


export async function apiPostForm(
    url,
    formData
) {

    const response =
        await fetch(url, {

            method: "POST",

            credentials:
                "same-origin",

            body: formData
        });

    return handleResponse(response);
}


async function handleResponse(
    response
) {

    if (!response.ok) {

        let errorMessage =
            "Request failed";

        try {

            const data =
                await response.json();

            errorMessage =
                data.error ||
                errorMessage;

        } catch (_) {}

        throw new Error(
            errorMessage
        );
    }

    return response.json();
}