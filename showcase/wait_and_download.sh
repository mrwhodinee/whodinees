#!/bin/bash
# Poll every 60 seconds until all models are done
cd /root/.openclaw/workspace/whodinees/showcase

for i in {1..10}; do
    echo "⏳ Check $i/10..."
    ./poll.sh
    
    # Check if all done by looking for "All models generated"
    if ./poll.sh 2>&1 | grep -q "All models generated"; then
        echo "✅ Complete!"
        exit 0
    fi
    
    if [ $i -lt 10 ]; then
        echo "Waiting 60s..."
        sleep 60
    fi
done

echo "⚠️  Timed out after 10 minutes"
exit 1
