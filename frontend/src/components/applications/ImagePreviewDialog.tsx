import React from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

interface ImagePreviewDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    imageUrl: string | null;
    title: string;
}

export const ImagePreviewDialog: React.FC<ImagePreviewDialogProps> = ({
                                                                          open,
                                                                          onOpenChange,
                                                                          imageUrl,
                                                                          title,
                                                                      }) => {
    if (!imageUrl) {
        return null;
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[90vw] max-h-[90vh] p-0">
                <DialogHeader className="p-4">
                    <DialogTitle>{title}</DialogTitle>
                </DialogHeader>
                <div className="flex justify-center items-center p-4 max-h-[80vh] overflow-auto">
                    <img
                        src={imageUrl}
                        alt={title}
                        className="max-w-full max-h-[80vh] object-contain"
                        onError={(e) => {
                            e.currentTarget.src = '/placeholder-image.jpg'; // Запасное изображение
                            e.currentTarget.onerror = null;
                        }}
                    />
                </div>
            </DialogContent>
        </Dialog>
    );
};