package cache

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/go-redis/redis/v8"
	. "github.com/winlp4ever/autocomplete-server/hint"
)

type Cache struct {
    rd *redis.Client
    ctx context.Context
}

func NewCache() *Cache {
	cache := new(Cache)
	cache.rd = redis.NewClient(&redis.Options{
        Addr:     "localhost:6379",
        Password: "", // no password set
        DB:       0,  // use default DB
    })
    cache.ctx = context.Background()
	return cache
}

// Cache hints in memory
func (c *Cache) Set(k string, v []Hint) error {
    js, err := json.Marshal(&v)
    if err != nil {
        return err
    }
    err = c.rd.Set(c.ctx, k, js, 0).Err()
    if err != nil {
        return err
    }
    return err
}

// Get cached hints
func (c *Cache) Get(k string) ([]Hint, error){
    enc, err := c.rd.Get(c.ctx, k).Result()
    if err == redis.Nil {
        return []Hint{}, err
    } else if err != nil {
        return []Hint{}, err
    }
    var hints []Hint
    err = json.Unmarshal([]byte(enc), &hints)
    if err != nil {
        return []Hint{}, err
    }
    return hints, err
}

func TestRedis() {
	cache := NewCache()

    err := cache.Set("key", []Hint{
        Hint{
            Id: 0,
            Text: "oof",
            Score: 0.25,
            Rep: "yay",
        },
    })
    if err != nil {
        panic(err)
    }

    val, err := cache.Get("key")
    if err != nil {
        panic(err)
    }
    fmt.Println("key", val)

    val2, err := cache.Get("kkt")
    if err == redis.Nil {
        fmt.Println("key2 does not exist")
    } else if err != nil {
        panic(err)
    } else {
        fmt.Println("key2", val2)
    }
}