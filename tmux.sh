#!/bin/sh
SESSION="Mr-Robot"

tmux new-session -d -s $SESSION -n "compose"
tmux send-keys -t $SESSION:compose "sudo docker-compose -f ./docker-compose-dev.yaml up" C-m

tmux new-window -t $SESSION -n neovim
tmux send-keys -t $SESSION:frontend "nvim ." C-m

tmux select-window -t $SESSION:compose

tmux attach-session -t $SESSION
