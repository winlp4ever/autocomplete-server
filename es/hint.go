package es

// Hint struct to be parsed to JSON
type Hint struct {
	Id int `json:"id"`
	Text string `json:"text"`
	Score float32 `json:"score"`
	Rep string `json:"rep"`
}

// default constructor
func NewHint(id int, text string, score float32, rep string) *Hint {
	hint := new(Hint)
	hint.Id = id 
	hint.Text = text 
	hint.Score = score 
	hint.Rep = rep
	return hint
}