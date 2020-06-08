package es

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"

	elasticsearch "github.com/elastic/go-elasticsearch/v8"
	. "github.com/winlp4ever/autocomplete-server/cache"
	. "github.com/winlp4ever/autocomplete-server/hint"
)

// Elastic Search Struct, init once with server
type Es struct {
	esClient *elasticsearch.Client
	cache *Cache
}

// Es Default Constructor
func NewEs() *Es {
	es := new(Es)
	e, err := elasticsearch.NewDefaultClient()
	// If err, raise error and return
	if err != nil {
		log.Fatalf("Error creating the client: %s", err)
	}
	es.esClient = e
	es.cache = NewCache()
	return es
}

// Return ElasticSearch Client info
func (e *Es) Info() {
	fmt.Println(e.esClient.Info())
} 

// Return hints of a question q by query for similar questions in elasticsearch db
func (es *Es) GetHints(q string) []Hint {
	hints, err := es.cache.Get(q)
	if err == nil {
		return hints
	}

	var (
		r  map[string]interface{}	  
		buf bytes.Buffer
	)
	
	// define the query
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
	if err := json.NewEncoder(&buf).Encode(query); err != nil {
		log.Fatalf("Error encoding query: %s", err)
	}

	// Perform the search request.
	res, err := es.esClient.Search(
		es.esClient.Search.WithContext(context.Background()),
		es.esClient.Search.WithIndex("qa"),
		es.esClient.Search.WithBody(&buf),
		es.esClient.Search.WithTrackTotalHits(true),
		es.esClient.Search.WithPretty(),
	)

	// If err, raise err and return
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

	results := []Hint{}
	reps := make(map[string]int)

	for _, hit := range r["hits"].(map[string]interface{})["hits"].([]interface{}) {
		doc := hit.(map[string]interface{})["_source"]
		rep := doc.(map[string]interface{})["rep"]
		rep_ := "-"
		if rep != nil {
			rep_ = rep.(string)
		}
		if _, ok := reps[rep_]; !ok {
			results = append(results, *NewHint(
				int(doc.(map[string]interface{})["id"].(float64)), 
				doc.(map[string]interface{})["text"].(string),
				float32(hit.(map[string]interface{})["_score"].(float64)),
				rep_,
			))
			reps[rep_] = 1
		}
	}
	es.cache.Set(q, results)
	return results
}