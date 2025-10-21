package util

import (
	"strings"
	"sync"

	"github.com/liuzl/gocc"
)

var (
	convOnce sync.Once
	convS2T  *gocc.OpenCC
	convT2S  *gocc.OpenCC
	convErr  error
)

func initConverters() {
	convOnce.Do(func() {
		convS2T, convErr = gocc.New("s2t")
		if convErr != nil {
			return
		}
		convT2S, convErr = gocc.New("t2s")
	})
}

func ToTraditional(text string) string {
	initConverters()
	if convErr != nil || convS2T == nil {
		return text
	}
	converted, err := convS2T.Convert(text)
	if err != nil {
		return text
	}
	return converted
}

func ToSimplified(text string) string {
	initConverters()
	if convErr != nil || convT2S == nil {
		return text
	}
	converted, err := convT2S.Convert(text)
	if err != nil {
		return text
	}
	return converted
}

func ExpandVariants(tokens []string) []string {
	seen := make(map[string]struct{})
	expanded := make([]string, 0, len(tokens)*3)
	for _, token := range tokens {
		token = strings.TrimSpace(token)
		if token == "" {
			continue
		}
		variants := []string{token}
		simplified := ToSimplified(token)
		traditional := ToTraditional(token)
		if simplified != token {
			variants = append(variants, simplified)
		}
		if traditional != token && traditional != simplified {
			variants = append(variants, traditional)
		}
		for _, v := range variants {
			if v == "" {
				continue
			}
			if _, ok := seen[v]; ok {
				continue
			}
			seen[v] = struct{}{}
			expanded = append(expanded, v)
		}
	}
	return expanded
}
