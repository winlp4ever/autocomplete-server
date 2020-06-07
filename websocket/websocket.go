package websocket

import (
	"bytes"
	"context"
	"encoding/json"
	"log"
	"strings"

	elasticsearch "github.com/elastic/go-elasticsearch/v8"
)

func TestEs() {

	var (
		r  map[string]interface{}	  
	)

	es, err := elasticsearch.NewDefaultClient()
    log.Println(elasticsearch.Version)
	log.Println(es.Info())

	if err != nil {
		log.Fatalf("Error creating the client: %s", err)
	}
	
	var buf bytes.Buffer

	q := `do while js`
	
	//json.Unmarshal([]byte(fieldsJson), &fields)
	query := map[string]interface{}{
		"query": map[string]interface{} {
			"multi_match": map[string]interface{}{
				"query": q,
				"type": "bool_prefix",
				"fields": []string {
					"text",
					"text._2gram",
					"text._3gram",
				},
			},
		},
		"size": 5,
		"_source": []string {
			"id", "text", "rep",
		},
	}
	query = map[string]interface{}{

	}
	if err := json.NewEncoder(&buf).Encode(query); err != nil {
		log.Fatalf("Error encoding query: %s", err)
	}

	// Perform the search request.
	res, err := es.Search(
		es.Search.WithContext(context.Background()),
		es.Search.WithIndex("qa"),
		es.Search.WithBody(&buf),
		es.Search.WithTrackTotalHits(true),
		es.Search.WithPretty(),
	)
	if err != nil {
		log.Fatalf("Error getting response: %s", err)
	}
	defer res.Body.Close()

	if res.IsError() {
		var e map[string]interface{}
		if err := json.NewDecoder(res.Body).Decode(&e); err != nil {
		log.Fatalf("Error parsing the response body: %s", err)
		} else {
		// Print the response status and error information.
		log.Fatalf("[%s] %s: %s",
			res.Status(),
			e["error"].(map[string]interface{})["type"],
			e["error"].(map[string]interface{})["reason"],
		)
		}
	}

	if err := json.NewDecoder(res.Body).Decode(&r); err != nil {
		log.Fatalf("Error parsing the response body: %s", err)
	}
	// Print the response status, number of results, and request duration.
	log.Printf(
		"[%s] %d hits; took: %dms",
		res.Status(),
		int(r["hits"].(map[string]interface{})["total"].(map[string]interface{})["value"].(float64)),
		int(r["took"].(float64)),
	)
	// Print the ID and document source for each hit.
	for _, hit := range r["hits"].(map[string]interface{})["hits"].([]interface{}) {
		doc := hit.(map[string]interface{})["_source"]
		log.Printf(" * ID=%s, %s, %f", 
			hit.(map[string]interface{})["_id"], 
			doc.(map[string]interface{})["text"],
			hit.(map[string]interface{})["_score"],
		)
	}

	log.Println(strings.Repeat("=", 37))
}