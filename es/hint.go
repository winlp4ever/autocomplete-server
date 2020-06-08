package es

type Hint struct {
	Id int `json:"id"`
	Text string `json:"text"`
	Score float32 `json:"score"`
}

// default constructor
func NewHint(id int, text string, score float32) *Hint {
	hint := new(Hint)
	hint.Id = id 
	hint.Text = text 
	hint.Score = score 
	return hint
}