package main

import (
	"encoding/json"
	"fmt"

	"github.com/gofiber/cors"
	"github.com/gofiber/fiber"
	"github.com/winlp4ever/autocomplete-server/es"
)

type TypedQuestion struct {
	Typing string `json:"typing"`
	ConversationID int16 `json:"conversationID"`
	Timestamp int64 `json:"timestamp"`
}

var e es.Es

func postHints(c *fiber.Ctx) {
	var msg TypedQuestion
	json.Unmarshal([]byte(c.Body()), &msg)
	
	hs := e.GetHints(msg.Typing)
	fmt.Println(hs)
	c.JSON(fiber.Map{
		"hints": hs,
		"conversationID": msg.ConversationID,
		"timestamp": msg.Timestamp,
	})
}

func main() {
	fmt.Println("ok")
	e = es.NewEs()

	app := fiber.New()
	app.Use(cors.New())

	app.Post("/post-hints", postHints)

	app.Listen(5600)
}
