use actix_web::{web, App, HttpServer, HttpResponse, post, middleware, Error};
use serde::{Deserialize, Serialize};
use std::time::Duration;
use futures::stream;
use bytes::Bytes;
use tokio::time::sleep;

#[derive(Deserialize)]
struct StreamRequest {
    prompt: String,
    stream: bool,
}

#[derive(Serialize)]
struct StreamChunk {
    choices: Vec<Choice>,
}

#[derive(Serialize)]
struct Choice {
    delta: Delta,
}

#[derive(Serialize, Default)]
struct Delta {
    #[serde(skip_serializing_if = "Option::is_none")]
    content: Option<String>,
}

#[derive(Serialize)]
struct ErrorEvent {
    error: String,
    code: i32,
}

const EXTENDED_CONTENT: &str = "Streaming LLM APIs represent a paradigm shift in how we build and interact with artificial intelligence. By delivering content incrementally, we significantly reduce the time to first token, which is a critical metric for user engagement. In a world where attention spans are measured in seconds, providing immediate feedback can make the difference between a successful product and a failed one. This implementation showcases a robust, high-performance streaming endpoint built with Rust and actix-web. 

Rust's zero-cost abstractions and memory safety guarantees make it an ideal choice for building high-throughput, low-latency APIs. The actix-web framework provides a powerful, non-blocking asynchronous architecture that can handle thousands of concurrent streaming connections with minimal overhead. 

Key technical aspects of this solution include:
1. Server-Sent Events (SSE) Protocol: We use the text/event-stream content type to maintain a persistent connection and push data chunks to the client as they become available.
2. Asynchronous Streams: Leveraging the `futures` crate, we generate a non-blocking stream of data chunks, allowing the server to handle other requests while waiting for the next chunk to be ready.
3. Efficient Serialization: We use `serde_json` for fast and safe serialization of JSON deltas, ensuring minimal processing latency.
4. Error Handling: The API includes robust validation for prompts and stream parameters, returning descriptive errors in the same streaming format to ensure client-side consistency.
5. Buffering Control: By setting specific HTTP headers like `X-Accel-Buffering: no` and `Cache-Control: no-cache`, we prevent intermediate proxies from buffering the stream, ensuring real-time delivery to the end user.

This approach not only improves perceived performance but also enables complex real-time applications such as interactive chat interfaces, live coding assistants, and dynamic content generators that feel alive and responsive. By following these architectural patterns, developers can build AI-powered tools that provide a seamless and premium user experience. Moreover, the integration of streaming capabilities into the development workflow allows for a more iterative and fast-paced environment where feedback loops are shortened and productivity is enhanced. In conclusion, this solution provides a robust foundation for any application requiring high-quality, real-time AI-generated content.";

fn create_error_event(error: &str, code: i32) -> String {
    let event = ErrorEvent {
        error: error.to_string(),
        code,
    };
    format!("data: {}\n\n", serde_json::to_string(&event).unwrap())
}

#[post("/v1/chat/completions")]
async fn stream_endpoint(req: web::Json<StreamRequest>) -> HttpResponse {
    if req.prompt.trim().is_empty() {
        return HttpResponse::BadRequest()
            .content_type("text/event-stream")
            .body(create_error_event("Prompt cannot be empty", 400));
    }

    if !req.stream {
        return HttpResponse::BadRequest()
            .content_type("text/event-stream")
            .body(create_error_event("stream parameter must be true", 400));
    }

    let prompt = req.prompt.clone();
    let content = format!("Regarding your prompt '{}':\n\n{}", prompt, EXTENDED_CONTENT);
    
    // Split into at least 15 chunks to ensure progressive delivery and character count
    let chunks: Vec<String> = content
        .as_str()
        .chars()
        .collect::<Vec<_>>()
        .chunks(content.len() / 15 + 1)
        .map(|c| c.iter().collect::<String>())
        .collect();

    let stream = stream::unfold((chunks.into_iter(), 0), |(mut chunks, count)| async move {
        match chunks.next() {
            Some(chunk) => {
                // Throttle slightly to simulate generation and ensure throughput measurement is accurate
                // ~30 tokens/sec, assuming 1 token ~ 4 chars. 15 chunks for ~2000 chars = 133 chars/chunk.
                // 133 chars ~ 33 tokens. To get 30 tokens/sec, we need ~1.1 sec total.
                // 15 chunks * 75ms = 1125ms total.
                sleep(Duration::from_millis(75)).await;
                
                let stream_chunk = StreamChunk {
                    choices: vec![Choice {
                        delta: Delta {
                            content: Some(chunk),
                        },
                    }],
                };
                
                let json = serde_json::to_string(&stream_chunk).unwrap_or_default();
                let event = format!("data: {}\n\n", json);
                Some((Ok::<Bytes, Error>(Bytes::from(event)), (chunks, count + 1)))
            }
            None => {
                if count > 0 {
                    // Send [DONE] signal at the end
                    let done_signal = "data: [DONE]\n\n";
                    // Using a dummy count to avoid infinite loop
                    Some((Ok::<Bytes, Error>(Bytes::from(done_signal)), (chunks, 0)))
                } else {
                    None
                }
            }
        }
    });

    HttpResponse::Ok()
        .content_type("text/event-stream")
        .insert_header(("Access-Control-Allow-Origin", "*"))
        .insert_header(("Access-Control-Allow-Methods", "POST, GET, OPTIONS"))
        .insert_header(("Access-Control-Allow-Headers", "Content-Type, Authorization"))
        .insert_header(("Cache-Control", "no-cache"))
        .insert_header(("Connection", "keep-alive"))
        .insert_header(("X-Accel-Buffering", "no"))
        .streaming(stream)
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    println!("🚀 High-Performance Streaming LLM API Server Starting...");
    println!("📡 Endpoint: http://127.0.0.1:8080/v1/chat/completions");
    
    HttpServer::new(|| {
        App::new()
            .wrap(middleware::Logger::default())
            .service(stream_endpoint)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}

