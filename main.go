package main

import (
	"fmt"

	"github.com/gofiber/fiber"
	"github.com/winlp4ever/autocomplete-server/websocket"
)

func main() {
	fmt.Println("ok")
	websocket.TestEs()
	app := fiber.New()

	app.Get("/", func(c *fiber.Ctx) {
		c.Send("Hello, World!")
	})

	app.Listen(3000)
}
