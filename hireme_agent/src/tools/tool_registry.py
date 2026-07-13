import json
from src.tools.job_search import search_jobs
from src.tools.job_scraper import scrape_job_listing

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": "Search for jobs on Adzuna based on keywords, location, and the requested number of results.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search keywords (e.g. 'python developer')."
                    },
                    "location": {
                        "type": "string",
                        "description": "The geographic location (e.g. 'London')."
                    },
                    "count": {
                        "type": "integer",
                        "description": "The number of job results to fetch."
                    }
                },
                "required": ["query", "location", "count"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_job_listing",
            "description": "Fetch and parse details of a job listing from its URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the job description page to scrape."
                    }
                },
                "required": ["url"]
            }
        }
    }
]

def execute_tool(tool_name: str, args: dict) -> str:
    """
    Executes the specified tool with the provided arguments and returns the result as a string.
    Prints a log message showing the tool name being executed.
    """
    print(f"Executing tool: {tool_name}")

    if tool_name == "search_jobs":
        query = args.get("query")
        location = args.get("location")
        count = args.get("count")
        
        # Handle count mapping safely in case string is passed
        try:
            count = int(count)
        except (ValueError, TypeError):
            count = 3
            
        results = search_jobs(query=query, location=location, count=count)
        return json.dumps(results)

    elif tool_name == "scrape_job_listing":
        url = args.get("url")
        result_text = scrape_job_listing(url=url)
        return result_text

    else:
        return f"Error: Tool '{tool_name}' is not recognized."
