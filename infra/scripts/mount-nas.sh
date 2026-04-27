#!/usr/bin/env bash
# Mount NAS shares from bucket.home onto the Mac via SMB.
#
# Prerequisites:
#   - Connect via Finder (⌘K → smb://bucket.home) once to store credentials in Keychain
#   - Mount points must be pre-created: sudo mkdir -p /Volumes/home /Volumes/plex /Volumes/pbin
#
# Usage:
#   ./scripts/mount-nas.sh          # mount all SMB shares
#   ./scripts/mount-nas.sh unmount  # unmount all

NAS_HOST="bucket.home"
NAS_USER="marcus"
SHARES=("home" "plex" "pbin")

mount_shares() {
    for share in "${SHARES[@]}"; do
        local mount_point="/Volumes/$share"

        if mount | grep -q " $mount_point "; then
            echo "$share: already mounted at $mount_point"
            continue
        fi

        if [ ! -d "$mount_point" ]; then
            echo "$share: mount point $mount_point does not exist — run: sudo mkdir -p $mount_point"
            continue
        fi

        echo "$share: mounting..."
        mount_smbfs "//$NAS_USER@$NAS_HOST/$share" "$mount_point" 2>&1

        if mount | grep -q " $mount_point "; then
            echo "$share: mounted at $mount_point"
        else
            echo "$share: FAILED — ensure SMB credentials are in Keychain (Finder → ⌘K → smb://bucket.home)"
        fi
    done
}

unmount_shares() {
    for share in "${SHARES[@]}"; do
        local mount_point="/Volumes/$share"

        if ! mount | grep -q " $mount_point "; then
            echo "$share: not mounted"
            continue
        fi

        echo "$share: unmounting..."
        umount "$mount_point" && echo "$share: unmounted" || echo "$share: FAILED to unmount"
    done
}

case "${1:-mount}" in
    unmount|umount) unmount_shares ;;
    *) mount_shares ;;
esac
